from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI
from datetime import datetime
import time
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB setup with Atlas URI
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client["mai_db"]
conversations = db["conversations"]

class MAI:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = os.getenv('ASSISTANT_ID')
        self.threads = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        try:
            thread = self._get_or_create_thread(user_id)
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            is_first_message = len(messages.data) == 0
            
            if is_first_message:
                initial_question = "What has you looking into MAI today?"
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="assistant",
                    content=initial_question
                )
                conversations.insert_one({
                    "user_id": user_id,
                    "question": initial_question,
                    "response": None,
                    "timestamp": datetime.now()
                })
                return initial_question
            
            # Log user response and pass to assistant
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )
            conversations.insert_one({
                "user_id": user_id,
                "question": "What has you looking into MAI today?",
                "response": message,
                "timestamp": datetime.now()
            })
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            response = self._wait_for_response(thread.id, run.id)
            return response
        
        except Exception as e:
            print(f"Error: {str(e)}")
            return "Sorry, something went wrong."
    
    def _get_or_create_thread(self, user_id: str):
        if user_id not in self.threads:
            thread = self.client.beta.threads.create()
            self.threads[user_id] = thread
        return self.threads[user_id]
    
    def _wait_for_response(self, thread_id: str, run_id: str) -> str:
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                return messages.data[0].content[0].text.value
            time.sleep(1)

mai = MAI()

@app.route('/')
def home():
    return "Welcome to MAI - Your Sales Assistant is live! Use /chat to interact."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    message = data.get('message', '')
    response = mai.process_message(user_id, message)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 