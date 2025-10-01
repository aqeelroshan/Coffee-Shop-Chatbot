# utils.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

RUNPOD_TOKEN = os.getenv("RUNPOD_TOKEN")
RUNPOD_CHATBOT_URL = os.getenv("RUNPOD_CHATBOT_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
RUNPOD_EMBEDDING_URL = os.getenv("RUNPOD_EMBEDDING_URL")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

def get_chatbot_response(model_name, messages, temperature=0):
    payload = {
        "input": {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.8,
            "max_tokens": 2000
        }
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(RUNPOD_CHATBOT_URL, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()

    try:
        # Get the first string inside tokens
        final_text = result["output"][0]["choices"][0]["tokens"][0]
    except (KeyError, IndexError, TypeError):
        final_text = "No output returned"

    # Return in OpenAI-style format
    return {
        "choices": [
            {"message": {"role": "assistant", "content": final_text}}
        ]
    }



def get_embedding(model_name, text_input):
    
    payload = {
        "input": {
            "model": model_name,
            "input": text_input
        }
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(RUNPOD_EMBEDDING_URL, json=payload, headers=headers)
    response.raise_for_status()

    result = response.json()

    # Parse RunPod embedding output
    try:
        embeddings = result["output"]["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError):
        embeddings = []

    return embeddings 













# guard_agent.py
from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response  # use your working utils

load_dotenv()

class GuardAgent():
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME")
    
    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        Your task is to determine whether the user is asking something relevant to the coffee shop or not.
        The user is allowed to:
        1. Ask questions about the coffee shop, like location, working hours, menu items and coffee shop related questions.
        2. Ask questions about menu items, they can ask for ingredients in an item and more details about the item.
        3. Make an order.
        4. Ask about recommendations of what to buy.

        The user is NOT allowed to:
        1. Ask questions about anything else other than our coffee shop.
        2. Ask questions about the staff or how to make a certain menu item.

        Your output should be in a structured json format like so. Each key is a string and each value is a string. Make sure to follow the format exactly:
        {
            "chain of thought": go over each of the points above and make see if the message lies under this point or not. Then you write some your thoughts about what point is this input relevant to.
            "decision": "allowed" or "not allowed". Pick one of those. and only write the word.
            "message": leave the message empty if it's allowed, otherwise write "Sorry, I can't help with that. Can I help you with your order?"
        }
        """
        
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        # Call RunPod via your utils function
        chatbot_output = get_chatbot_response(self.model_name, input_messages)
        
        # Post-process and structure the output
        output = self.postprocess(chatbot_output)
        return output

    def postprocess(self, output):
        # The utils function returns OpenAI-style dict, so extract the message content
        try:
            text_output = output["choices"][0]["message"]["content"]
            json_output = json.loads(text_output)
        except (KeyError, IndexError, json.JSONDecodeError):
            json_output = {
                "chain of thought": "",
                "decision": "not allowed",
                "message": "Sorry, I can't help with that. Can I help you with your order?"
            }

        dict_output = {
            "role": "assistant",
            "content": json_output.get('message', ""),
            "memory": {
                "agent": "guard_agent",
                "guard_decision": json_output.get('decision', "not allowed")
            }
        }
        return dict_output


















# classification_agent.py
from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response

load_dotenv()

class ClassificationAgent():
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME")
    
    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop application.
        Your task is to determine what agent should handle the user input. You have 3 agents to choose from:
        1. details_agent: This agent answers questions about the coffee shop, like location, delivery places, working hours, details about menu items, or listing items in the menu.
        2. order_taking_agent: This agent takes orders from the user. It's responsible for conversing with the user about the order until it's complete.
        3. recommendation_agent: This agent gives recommendations about what to buy if the user asks for a recommendation.

        Your output should be in a structured JSON format like so. Each key is a string and each value is a string. Make sure to follow the format exactly:
        {
            "chain of thought": go over each of the agents above and write your thoughts about which agent this input is relevant to.
            "decision": "details_agent" or "order_taking_agent" or "recommendation_agent". Pick one of those, and only write the word.
            "message": leave the message empty.
        }
        """

        # Take the last 3 messages for context
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        # Call RunPod via your utils function
        chatbot_output = get_chatbot_response(self.model_name, input_messages)

        # Post-process and structure the output
        output = self.postprocess(chatbot_output)
        return output

    def postprocess(self, output):
        # Extract message content safely
        try:
            text_output = output["choices"][0]["message"]["content"]
            json_output = json.loads(text_output)
        except (KeyError, IndexError, json.JSONDecodeError):
            json_output = {
                "chain of thought": "",
                "decision": "details_agent",
                "message": ""
            }

        dict_output = {
            "role": "assistant",
            "content": json_output.get('message', ""),
            "memory": {
                "agent": "classification_agent",
                "classification_decision": json_output.get('decision', "details_agent")
            }
        }
        return dict_output
