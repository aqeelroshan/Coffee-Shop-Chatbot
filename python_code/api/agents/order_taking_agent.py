from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response , double_check_json_output
load_dotenv()

class OrderTakingAgent():
    def __init__(self, recommendation_agent):
        
        self.model_name = os.getenv("MODEL_NAME")
        self.api_url = os.getenv("RUNPOD_CHATBOT_URL")
        self.api_key = os.getenv("RUNPOD_TOKEN")
        self.recommendation_agent = recommendation_agent
        
    
    def get_response(self,messages):
        messages = deepcopy(messages)
        system_prompt = """
You are a customer support bot for a coffee shop called "Mug Life".

Here is the menu:
Cappuccino - ₹300.00
Jumbo Savory Scone - ₹250.00
Latte - ₹390.00
Chocolate Chip Biscotti - ₹200.00
Espresso shot - ₹160.00
Hazelnut Biscotti - ₹220.00
Chocolate Croissant - ₹300.00
Dark chocolate (Drinking Chocolate) - ₹400.00
Cranberry Scone - ₹290.00
Croissant - ₹250.00
Almond Croissant - ₹330.00
Ginger Biscotti - ₹200.50
Oatmeal Scone - ₹250.00
Ginger Scone - ₹290.00
Chocolate syrup - ₹120.00
Hazelnut syrup - ₹140.00
Carmel syrup - ₹130.00
Sugar Free Vanilla syrup - ₹130.00
Dark chocolate (Packaged Chocolate) - ₹250.00

Rules:
- DO NOT talk about payments or counters.
- DO NOT ask the user to go anywhere.

Steps:
1. Take the order.
2. Validate items against menu.
3. If invalid, notify and confirm valid items.
4. Ask if they want more.
5. Repeat if yes.
6. If no, output the final order summary, total, and thank them.

Output Rules:
- You MUST return ONLY a single valid JSON object.
- No explanations, no extra text, no markdown formatting.
- Every key and value must be a string, except "order" which is a JSON array.

JSON format (exactly this):
{
"chain of thought": "One short sentence (max 15 words) explaining reasoning.",
"step number": "The current step number.",
"order": "[{\"item\": \"item name\", \"quantity\": \"number\", \"price\": \"total price\"}]",
"response": "Your response to the user."
}
"""



        last_order_taking_status = ""
        asked_recommendation_before = False
        for message_index in range(len(messages)-1,0,-1):
            message = messages[message_index]
            
            agent_name = message.get("memory",{}).get("agent","")
            if message["role"] == "assistant" and agent_name == "order_taking_agent":
                step_number = message["memory"]["step number"]
                order = message["memory"]["order"]
                asked_recommendation_before = message["memory"]["asked_recommendation_before"]
                last_order_taking_status = f"""
                step number: {step_number}
                order: {order}
                """
                break

        messages[-1]['content'] = last_order_taking_status + " \n "+ messages[-1]['content']

        input_messages = [{"role": "system", "content": system_prompt}] + messages        

        chatbot_output = get_chatbot_response(self.model_name,input_messages)

        # double check json 
        chatbot_output = double_check_json_output(self.model_name,chatbot_output)

        output = self.postprocess(chatbot_output, messages, asked_recommendation_before)

        return output

    # def postprocess(self,output,messages,asked_recommendation_before):
    #     output = json.loads(output)

    #     if type(output["order"]) == str:
    #         output["order"] = json.loads(output["order"])

    #     response = output['response']
    #     if not asked_recommendation_before and len(output["order"])>0:
    #         recommendation_output = self.recommendation_agent.get_recommendations_from_order(messages,output['order'])
    #         response = recommendation_output['content']
    #         asked_recommendation_before = True

    #     dict_output = {
    #         "role": "assistant",
    #         "content": response ,
    #         "memory": {"agent":"order_taking_agent",
    #                    "step number": output["step number"],
    #                    "order": output["order"],
    #                    "asked_recommendation_before": asked_recommendation_before
    #                   }
    #     }

        
    #     return dict_output
    
    
    
    
    def postprocess(self, output, messages, asked_recommendation_before):
        output = json.loads(output)

        # ✅ Defensive: Ensure "order" is always a Python list
        if isinstance(output.get("order"), str):
            try:
                output["order"] = json.loads(output["order"])
            except json.JSONDecodeError:
                output["order"] = []

        # ✅ Defensive: Ensure "step number" always exists
        step_number = output.get("step number", "1")

        # ✅ Defensive: Ensure "response" always exists
        response = output.get("response", "")

        # If we haven’t yet asked for recommendations, call recommendation agent
        if not asked_recommendation_before and len(output["order"]) > 0:
            recommendation_output = self.recommendation_agent.get_recommendations_from_order(
                messages, output["order"]
            )
            response = recommendation_output.get("content", response)
            asked_recommendation_before = True

        dict_output = {
            "role": "assistant",
            "content": response,
            "memory": {
                "agent": "order_taking_agent",
                "step number": step_number,  # ✅ fallback applied
                "order": output.get("order", []),
                "asked_recommendation_before": asked_recommendation_before,
            },
        }

        return dict_output
