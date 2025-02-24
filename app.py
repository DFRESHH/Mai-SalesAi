from flask import Flask, request, jsonify, render_template
import openai
from openai import OpenAI
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from flask_cors import CORS
import nest_asyncio
import time

# Load environment variables from .env file
load_dotenv()

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Validate essential environment variables
required_env_vars = ['OPENAI_API_KEY', 'ASSISTANT_ID']
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Error: {var} is missing. Check your .env file.")

@dataclass
class Interaction:
    """Records details about each customer interaction"""
    user_id: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    response: Optional[str] = None

class MAI:
    """Main class handling all of MAI's capabilities"""
    
    def __init__(self):
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai
        self.assistant_id = os.getenv('ASSISTANT_ID')
        
        # Initialize conversation tracking (in-memory only)
        self.threads = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a message using the OpenAI Assistant"""
        try:
            # Create interaction record (no storage)
            interaction = Interaction(
                user_id=user_id,
                message=message,
                timestamp=datetime.now(),
                context=self._get_context(user_id)
            )
            
            # Get or create thread for this user
            thread = self._get_or_create_thread(user_id)
            
            # Add message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )
            
            # Run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for response
            response = self._wait_for_response(thread.id, run.id)
            
            # Update interaction with response (in-memory only)
            interaction.response = response
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return "I apologize, but I encountered an error processing your message."
    
    def _get_or_create_thread(self, user_id: str):
        """Get existing thread or create new one for user"""
        if user_id not in self.threads:
            thread = self.client.beta.threads.create()
            self.threads[user_id] = thread
        return self.threads[user_id]
    
    def _wait_for_response(self, thread_id: str, run_id: str) -> str:
        """Wait for and retrieve the assistant's response"""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                return messages.data[0].content[0].text.value
            
            elif run.status == "failed":
                return "I apologize, but I encountered an error processing your request."
            
            time.sleep(1)
    
    def _get_context(self, user_id: str) -> Dict:
        """Retrieve context for a user (stub since no MongoDB)"""
        return {'previous_interactions': [], 'learning_patterns': {}}

# Initialize MAI instance
mai = MAI()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        response = mai.process_message(user_id, message)
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset a user's conversation"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        if user_id in mai.threads:
            del mai.threads[user_id]
        
        return jsonify({'message': 'Conversation reset successfully'})
        
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)