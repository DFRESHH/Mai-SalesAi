from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI
from datetime import datetime
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

class MAI:
    """Main class handling all of MAI's capabilities"""
    
    def __init__(self):
        # Initialize OpenAI
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = os.getenv('ASSISTANT_ID')
        # Initialize conversation tracking
        self.threads = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a message using the OpenAI Assistant"""
        try:
            # Get or create thread for this user
            thread = self._get_or_create_thread(user_id)
            
            # Check if this is the first message in the thread
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            is_first_message = len(messages.data) == 0
            
            # If it's the first message, send a welcome message
            if is_first_message:
                initial_question = f"Hi {user_id}, I am Mia your virtual sales assistant, what has you looking into my site today?"
                return initial_question
            
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
            response = self._wait_for_response(thread.id, run.id, timeout=25)
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error processing your message: {str(e)}"
    
    def _get_or_create_thread(self, user_id: str):
        """Get existing thread or create new one for user"""
        if user_id not in self.threads:
            thread = self.client.beta.threads.create()
            self.threads[user_id] = thread
        return self.threads[user_id]
    
    def _wait_for_response(self, thread_id: str, run_id: str, timeout: int = 30) -> str:
        """Wait for and retrieve the assistant's response with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                return messages.data[0].content[0].text.value
            
            elif run.status in ["failed", "cancelled"]:
                return "I apologize, but I encountered an error processing your request."
            
            time.sleep(0.5)  # Check more frequently but with less load
        
        return "I'm sorry, but it's taking longer than expected to process your request. Please try again."

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
        
        return jsonify({'status': 'reset successful'})
        
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    # Print startup message
    print("Starting MAI Training Interface...")
    print(f"OpenAI API Key: {'Present' if os.getenv('OPENAI_API_KEY') else 'Missing'}")
    print(f"Assistant ID: {'Present' if os.getenv('ASSISTANT_ID') else 'Missing'}")
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
