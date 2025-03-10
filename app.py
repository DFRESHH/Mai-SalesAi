from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask_cors import CORS
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

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
    response: Optional[str] = None

class MAI:
    """Main class handling all of MAI's capabilities"""
    
    def __init__(self):
        # Initialize OpenAI - SIMPLIFIED TO AVOID PROXIES ERROR
        try:
            # Just create the client with the API key, no additional parameters
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.assistant_id = os.getenv('ASSISTANT_ID')
            print(f"Successfully initialized OpenAI client with assistant ID: {self.assistant_id}")
        except Exception as e:
            print(f"Error initializing OpenAI client: {str(e)}")
            raise
        
        # Initialize conversation tracking
        self.threads = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a message using the OpenAI Assistant"""
        try:
            print(f"Processing message for user {user_id}")
            
            # Create interaction record
            interaction = Interaction(
                user_id=user_id,
                message=message,
                timestamp=datetime.now()
            )
            
            # Get or create thread for this user
            try:
                thread = self._get_or_create_thread(user_id)
                print(f"Using thread ID: {thread.id}")
            except Exception as e:
                print(f"ERROR creating/getting thread: {str(e)}")
                import traceback
                print(traceback.format_exc())
                return "I apologize, but I encountered an error setting up our conversation."
            
            # Add message to thread
            try:
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                print(f"Added message to thread {thread.id}")
            except Exception as e:
                print(f"Error adding message to thread: {str(e)}")
                return "I apologize, but I encountered an error processing your message."
            
            # Run assistant
            try:
                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=self.assistant_id
                )
                print(f"Created run {run.id} for thread {thread.id}")
            except Exception as e:
                print(f"Error creating run: {str(e)}")
                return "I apologize, but I encountered an error running the assistant."
            
            # Wait for response
            try:
                response = self._wait_for_response(thread.id, run.id)
                print(f"Got response: {response[:50]}...")
            except Exception as e:
                print(f"Error waiting for response: {str(e)}")
                return "I apologize, but I encountered an error getting a response."
            
            # Update interaction with response
            interaction.response = response
            
            return response
            
        except Exception as e:
            print(f"Unexpected error in process_message: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return "I apologize, but I encountered an unexpected error processing your message."
    
    def _get_or_create_thread(self, user_id: str):
        """Get existing thread or create new one for user"""
        if user_id not in self.threads:
            thread = self.client.beta.threads.create()
            self.threads[user_id] = thread
        return self.threads[user_id]
    
    def _wait_for_response(self, thread_id: str, run_id: str) -> str:
        """Wait for and retrieve the assistant's response"""
        print(f"Waiting for response on thread {thread_id}, run {run_id}")
        
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            print(f"Run status: {run.status}")
            
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                return messages.data[0].content[0].text.value
            
            elif run.status == "failed":
                print(f"Run failed with error: {getattr(run, 'last_error', 'Unknown error')}")
                return "I apologize, but I encountered an error processing your request."
            
            time.sleep(1)

# Initialize MAI instance
mai = MAI()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        print("Chat endpoint called")
        data = request.get_json()
        print(f"Request data: {data}")
        
        user_id = data.get('user_id', 'default_user')
        message = data.get('message')
        
        print(f"User ID: {user_id}, Message: {message}")
        
        if not message:
            print("Error: No message provided")
            return jsonify({'error': 'Message is required'}), 400
        
        print(f"Processing message with OpenAI assistant {os.getenv('ASSISTANT_ID')}")
        
        response = mai.process_message(user_id, message)
        print(f"Response generated: {response[:50]}...")
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"ERROR in chat endpoint: {str(e)}")
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Traceback: {error_traceback}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

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

@app.route('/debug', methods=['GET'])
def debug():
    """Debug endpoint to test basic functionality"""
    try:
        # Test OpenAI connection
        try:
            models = mai.client.models.list()
            openai_status = f"Connected (found {len(models.data)} models)"
        except Exception as e:
            openai_status = f"Error: {str(e)}"
        
        # Test Assistant ID
        try:
            assistant = mai.client.beta.assistants.retrieve(assistant_id=mai.assistant_id)
            assistant_status = f"Found: {assistant.name}"
        except Exception as e:
            assistant_status = f"Error: {str(e)}"
        
        return jsonify({
            'environment': os.environ.get('FLASK_ENV', 'not set'),
            'openai_api': openai_status,
            'assistant': assistant_status,
            'threads_count': len(mai.threads)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    