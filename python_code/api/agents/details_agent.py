from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response, get_embedding, double_check_json_output
from pinecone import Pinecone

load_dotenv()

class DetailsAgent():
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME")
        self.api_url = os.getenv("RUNPOD_CHATBOT_URL")
        self.api_key = os.getenv("RUNPOD_TOKEN")
        self.embedding_url = os.getenv("RUNPOD_EMBEDDING_URL")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
        
        # Pinecone setup
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.pc_api_key = os.getenv("PINECONE_API_KEY")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.pc_api_key)  # create client instance
        self.index = self.pc.Index(self.index_name)  # access your index
        
        
    def get_closest_results(self,index_name,input_embeddings,top_k=2):
        index = self.pc.Index(index_name)
        
        results = index.query(
            namespace="ns1",
            vector=input_embeddings,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return results
    
    
    def get_response(self,messages):
        messages = deepcopy(messages)

        user_message = messages[-1]['content']
        embedding = get_embedding(self.embedding_model_name,user_message)
        result = self.get_closest_results(self.index_name,embedding)
        source_knowledge = "\n".join([x['metadata']['text'].strip()+'\n' for x in result['matches'] ])

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = """
You are a customer support agent for a coffee shop called Mug Life.
You act like a polite waiter.
You should answer questions ONLY about the coffee shop and its menu.

Output: Respond in plain text to the user (no JSON needed).
"""

        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.model_name,input_messages)
        chatbot_output = double_check_json_output(self.model_name, chatbot_output)
        output = self.postprocess(chatbot_output)
        return output
    
    
    def postprocess(self, output):

        return {
            "role": "assistant",
            "content": output,
            "memory": {"agent": "details_agent"}
        }


