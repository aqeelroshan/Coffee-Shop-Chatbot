from dotenv import load_dotenv
import os
import pandas as pd
import json
import re
from copy import deepcopy
from .utils import get_chatbot_response, double_check_json_output
load_dotenv()

class RecommendationAgent():
    def __init__(self,apriori_recommendation_path,popular_recommendation_path):
        
        self.model_name = os.getenv("MODEL_NAME")
        self.api_url = os.getenv("RUNPOD_CHATBOT_URL")
        self.api_key = os.getenv("RUNPOD_TOKEN")
        
        with open(apriori_recommendation_path, 'r') as file:
            self.apriori_recommendations = json.load(file)

        self.popular_recommendations = pd.read_csv(popular_recommendation_path)
        self.products = self.popular_recommendations['product'].tolist()
        self.product_categories = self.popular_recommendations['product_category'].tolist()
    
    def get_apriori_recommendation(self,products,top_k=5):
        recommendation_list = []
        for product in products:
            if product in self.apriori_recommendations:
                recommendation_list += self.apriori_recommendations[product]
        
        # Sort recommendation list by "confidence"
        recommendation_list = sorted(recommendation_list,key=lambda x: x['confidence'],reverse=True)

        recommendations = []
        recommendations_per_category = {}
        for recommendation in recommendation_list:
            # If Duplicated recommendations then skip
            if recommendation in recommendations:
                continue 

            # Limit 2 recommendations per category
            product_catory = recommendation['product_category']
            if product_catory not in recommendations_per_category:
                recommendations_per_category[product_catory] = 0
            
            if recommendations_per_category[product_catory] >= 2:
                continue

            recommendations_per_category[product_catory]+=1

            # Add recommendation
            recommendations.append(recommendation['product'])

            if len(recommendations) >= top_k:
                break

        return recommendations 

    def get_popular_recommendation(self,product_categories=None,top_k=5):
        recommendations_df = self.popular_recommendations
        
        if type(product_categories) == str:
            product_categories = [product_categories]

        if product_categories is not None:
            recommendations_df = self.popular_recommendations[self.popular_recommendations['product_category'].isin(product_categories)]
        recommendations_df = recommendations_df.sort_values(by='number_of_transactions',ascending=False)
        
        if recommendations_df.shape[0] == 0:
            return []

        recommendations = recommendations_df['product'].tolist()[:top_k]
        return recommendations

    def recommendation_classification(self,messages):
        system_prompt = """
You are a helpful AI assistant for a coffee shop application which serves drinks and pastries. 
Your ONLY task is to provide recommendations.

Recommendation types:
1. apriori → Based on user’s order history (items bought together).
2. popular → Based on general popularity.
3. popular by category → Based on popular items in a requested category.

Items in the coffee shop:
""" + ",".join(self.products) + """
Categories in the coffee shop:
""" + ",".join(self.product_categories) + """

Output Rules:
- You MUST return ONLY a single valid JSON object.
- No explanations, no extra text, no markdown formatting.
- Every key and value must be a string (except "parameters", which is a Python list).

JSON format (exactly this):
{
"chain of thought": "Explain briefly why this is apriori, popular, or popular by category.",
"recommendation_type": "apriori" or "popular" or "popular by category",
"parameters": [list of items or categories, or empty list]
}
"""

        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.model_name,input_messages)
        chatbot_output = double_check_json_output(self.model_name, chatbot_output)
        output = self.postprocess_classification(chatbot_output)
        return output

    def get_response(self,messages):
        messages = deepcopy(messages)

        recommendation_classification = self.recommendation_classification(messages)
        recommendation_type = recommendation_classification['recommendation_type']
        recommendations = []
        if recommendation_type == "apriori":
            recommendations = self.get_apriori_recommendation(recommendation_classification['parameters'])
        elif recommendation_type == "popular":
            recommendations = self.get_popular_recommendation()
        elif recommendation_type == "popular by category":
            recommendations = self.get_popular_recommendation(recommendation_classification['parameters'])
        
        if recommendations == []:
            return {"role": "assistant", "content":"Sorry, I can't help with that. Can I help you with your order?"}
        
        # Respond to User
        recommendations_str = ", ".join(recommendations)
        
        system_prompt = f"""
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        your task is to recommend items to the user based on their input message. And respond in a friendly but concise way. And put it an unordered list with a very small description.

        I will provide what items you should recommend to the user based on their order in the user message. 
        """

        prompt = f"""
        {messages[-1]['content']}

        Please recommend me those items exactly: {recommendations_str}
        """

        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.model_name,input_messages)
        output = self.postprocess(chatbot_output)

        return output



    # def postprocess_classfication(self,output):
    #     output = json.loads(output)

    #     dict_output = {
    #         "recommendation_type": output['recommendation_type'],
    #         "parameters": output['parameters'],
    #     }
    #     return dict_output
    
    
  

    def postprocess_classification(self, output: str):
        # 1. Ensure output is not empty
        if not output or not output.strip():
            raise ValueError("Empty output from chatbot response")

        parsed = None

        # 2. Try direct JSON load
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            # 3. Extract the first {...} block from the text
            match = re.search(r"\{.*\}", output, re.DOTALL)
            if not match:
                raise ValueError(f"No JSON object found in output: {output}")

            json_str = match.group(0)

            # 4. Try loading again
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                # 5. Attempt simple fixes for unquoted values
                fixed = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)', r': "\1"', json_str)
                parsed = json.loads(fixed)

        # 6. Build dictionary safely
        dict_output = {
            "recommendation_type": parsed.get("recommendation_type", "unknown"),
            "parameters": parsed.get("parameters", []),
        }
        return dict_output

    
    

    def get_recommendations_from_order(self,messages,order):
        products = []
        for product in order:
            products.append(product['item'])

        recommendations = self.get_apriori_recommendation(products)
        recommendations_str = ", ".join(recommendations)

        system_prompt = f"""
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        your task is to recommend items to the user based on their order.

        I will provide what items you should recommend to the user based on their order in the user message. 
        """

        prompt = f"""
        {messages[-1]['content']}

        Please recommend me those items exactly: {recommendations_str}
        """

        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.model_name,input_messages)
        output = self.postprocess(chatbot_output)

        return output
    
    def postprocess(self,output):
        output = {
            "role": "assistant",
            "content": output,
            "memory": {"agent":"recommendation_agent"
                      }
        }
        return output