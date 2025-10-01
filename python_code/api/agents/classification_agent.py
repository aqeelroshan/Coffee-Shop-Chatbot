from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response , double_check_json_output
load_dotenv()

class ClassificationAgent():
    def __init__(self):
        
        self.model_name = os.getenv("MODEL_NAME")
        self.api_url = os.getenv("RUNPOD_CHATBOT_URL")
        self.api_key = os.getenv("RUNPOD_TOKEN")
        
    def get_response(self,messages):
        messages = deepcopy(messages)

        system_prompt = """
You are a helpful AI assistant for a coffee shop application.
Your ONLY task is to classify the user input to the correct agent.

Agents:
1. details_agent → For coffee shop info (location, delivery, hours, menu item details, listing items).
2. order_taking_agent → For handling user orders.
3. recommendation_agent → For recommending items.

Output Rules:
- You MUST return ONLY a single valid JSON object.
- No explanations, no extra text, no markdown formatting.
- Every key and value must be a string.

JSON format (exactly this):
{
"chain_of_thought": "Brief reasoning in one sentence.",
"decision": "details_agent" or "order_taking_agent" or "recommendation_agent",
"message": ""
}
"""




        
        input_messages = [
            {"role": "system", "content": system_prompt},
        ]

        input_messages += messages[-3:]

        chatbot_output =get_chatbot_response(self.model_name,input_messages)
        chatbot_output = double_check_json_output(self.model_name, chatbot_output)
        output = self.postprocess(chatbot_output)
        return output

    def postprocess(self,output):
        output = json.loads(output)

        dict_output = {
            "role": "assistant",
            "content": output['message'],
            "memory": {"agent":"classification_agent",
                       "classification_decision": output['decision']
                      }
        }
        return dict_output