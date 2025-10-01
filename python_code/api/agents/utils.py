# utils.py
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

RUNPOD_TOKEN = os.getenv("RUNPOD_TOKEN")
RUNPOD_CHATBOT_URL = os.getenv("RUNPOD_CHATBOT_URL")
RUNPOD_EMBEDDING_URL = os.getenv("RUNPOD_EMBEDDING_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
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

    # Return only string
    return final_text


    
    



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




import json
import re

def double_check_json_output(model_name, json_string, max_retries=2):
    """
    Ensures the model output is always valid JSON.
    Cleans up any extra text/formatting before returning.
    """

    def clean_json(text):
        # Remove code fences like ```json ... ```
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
        # Extract JSON object using regex (first {...} block)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    prompt = f"""
    You are a JSON validator.
    You will ONLY return a valid JSON object.
    If the input is valid JSON, return it exactly as is.
    If it's invalid, fix formatting/errors so it becomes valid JSON.
    Do NOT add explanations, notes, or markdown. Return ONLY the JSON.

    Input:
    {json_string}
    """

    messages = [{"role": "user", "content": prompt}]
    response = get_chatbot_response(model_name, messages)

    # Clean up response
    response = clean_json(response)

    # Try parsing, retry if needed
    for _ in range(max_retries):
        try:
            json.loads(response)  # validate JSON
            return response
        except json.JSONDecodeError:
            # Ask the model again to correct
            correction_prompt = f"""
            Fix this string so it becomes valid JSON. 
            Return ONLY the corrected JSON, nothing else:

            {response}
            """
            messages = [{"role": "user", "content": correction_prompt}]
            response = get_chatbot_response(model_name, messages)
            response = clean_json(response)

    # Final attempt: if still invalid, raise error
    raise ValueError("Model could not produce valid JSON after retries.")




import json
import re
from .utils import get_chatbot_response

def check_guard_json(model_name, json_string):
    """
    Ensures GuardAgent output is always valid JSON with expected keys.
    Returns a string of valid JSON.
    """

    # Remove extra formatting
    json_string = re.sub(r"^```(?:json)?|```$", "", json_string.strip(), flags=re.MULTILINE)
    match = re.search(r"\{.*\}", json_string, re.DOTALL)
    if match:
        json_string = match.group(0)

    # Try parsing
    try:
        data = json.loads(json_string)
        # Ensure required keys exist
        for key in ["chain of thought", "decision", "message"]:
            if key not in data:
                data[key] = ""
        return json.dumps(data)  # return as JSON string
    except json.JSONDecodeError:
        # If invalid, return safe default
        return json.dumps({
            "chain of thought": "",
            "decision": "not allowed",
            "message": "I apologize, but I can only assist with questions about MugLife, our menu, or your order."
        })
