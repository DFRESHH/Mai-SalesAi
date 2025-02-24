from flask import Flask, request, jsonify, render_template
import openai
from openai import OpenAI
import os
import json
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pymongo import MongoClient
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
    success_metrics: Dict[str, Any] = None

class MAI:
    """Main class handling all of MAI's capabilities"""
    
    def __init__(self):
       # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai
        self.assistant_id = os.getenv('ASSISTANT_ID')   
        
        pass

        # Initialize MongoDB connection
        try:
            # Get MongoDB URI from environment variable
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')  # Fallback for local dev
            self.mongo_client = MongoClient(mongo_uri)
            self.db = self.mongo_client['mai_database']
            # Create collections if they don't exist
            if 'conversations' not in self.db.list_collection_names():
                self.db.create_collection('conversations')
            if 'learnings' not in self.db.list_collection_names():
                self.db.create_collection('learnings')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
        
        # Initialize conversation tracking
        self.threads = {}
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a message using both the OpenAI Assistant and MongoDB learning system"""
        try:
            # Create interaction record
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
            
            # Update interaction with response
            interaction.response = response
            
            # Store interaction in MongoDB
            self._store_interaction(interaction)
            
            # Update learning patterns
            self._update_learning_patterns(interaction)
            
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
        """Retrieve context for a user from MongoDB"""
        context = {
            'previous_interactions': self._get_previous_interactions(user_id),
            'learning_patterns': self._get_learning_patterns(user_id)
        }
        return context
    
    def _store_interaction(self, interaction: Interaction):
        """Store interaction in MongoDB with size limits"""
        # Limit context size by only storing essential information
        limited_context = {
            'previous_interactions': interaction.context.get('previous_interactions', [])[-3:],
            'learning_patterns': interaction.context.get('learning_patterns', {})
        }
        
        # Create document with size limits
        document = {
            'user_id': interaction.user_id,
            'message': interaction.message[:10000],
            'response': interaction.response[:10000] if interaction.response else None,
            'timestamp': interaction.timestamp,
            'context': limited_context
        }
        
        try:
            self.db.conversations.insert_one(document)
        except Exception as e:
            print(f"Error storing interaction: {e}")
            # Fallback: Store without context if still too large
            document.pop('context')
            self.db.conversations.insert_one(document)
    
    def _get_previous_interactions(self, user_id: str, limit: int = 3) -> List[Dict]:
        """Get recent interactions for a user with limited fields"""
        return list(self.db.conversations
                   .find(
                       {'user_id': user_id},
                       {'message': 1, 'response': 1, 'timestamp': 1, '_id': 0}
                   )
                   .sort('timestamp', -1)
                   .limit(limit))
    
    def _get_learning_patterns(self, user_id: str) -> Dict:
        """Get learning patterns for a user"""
        return self.db.learnings.find_one({'user_id': user_id}) or {}
    
    def _update_learning_patterns(self, interaction: Interaction):
        """Update learning patterns based on interaction"""
        patterns = {
            'timestamp': interaction.timestamp,
            'user_id': interaction.user_id,
            'patterns_identified': self._analyze_patterns(interaction)
        }
        self.db.learnings.insert_one(patterns)
    
    def _analyze_patterns(self, interaction: Interaction) -> Dict:
        """Analyze interaction for patterns"""
        try:
            return {
                'interaction_type': {
                    'question_asked': self._contains_question(interaction.message),
                    'response_length': len(interaction.response) if interaction.response else 0,
                    'topic_category': self._categorize_topic(interaction.message)
                },
                'sales_patterns': {
                    'techniques_used': self._identify_sales_techniques(interaction.response),
                    'objections_raised': self._identify_objections(interaction.message),
                    'closing_attempts': []
                },
                'learning_metrics': {
                    'understanding_level': self._assess_understanding(interaction),
                    'engagement_score': 0.0,
                    'progress_indicators': []
                }
            }
        except Exception as e:
            print(f"Error in pattern analysis: {e}")
            return {}

    def _contains_question(self, message: str) -> bool:
        """Check if message contains questions"""
        return '?' in message

    def _categorize_topic(self, message: str) -> str:
        """Categorize the topic of discussion"""
        keywords = {
            'pricing': ['price', 'cost', 'budget', 'expensive', 'cheap'],
            'product': ['product', 'feature', 'specification', 'works'],
            'objection': ['worried', 'concern', 'problem', 'issue'],
            'closing': ['buy', 'purchase', 'deal', 'contract']
        }
        
        message = message.lower()
        for category, words in keywords.items():
            if any(word in message for word in words):
                return category
        return 'general'

    def _identify_sales_techniques(self, response: str) -> List[str]:
        """Identify sales techniques used in response"""
        techniques = []
        if response:
            response = response.lower()
            if '?' in response:
                techniques.append('questioning')
            if 'benefit' in response or 'value' in response:
                techniques.append('value_selling')
            if 'understand' in response or 'tell me more' in response:
                techniques.append('active_listening')
            if 'example' in response or 'instance' in response:
                techniques.append('storytelling')
        return techniques

    def _identify_objections(self, message: str) -> List[str]:
        """Identify any objections in the message"""
        objections = []
        message = message.lower()
        if any(word in message for word in ['expensive', 'cost', 'price']):
            objections.append('pricing')
        if any(word in message for word in ['time', 'waiting', 'long']):
            objections.append('timing')
        if any(word in message for word in ['competition', 'competitor']):
            objections.append('competition')
        return objections

    def _assess_understanding(self, interaction: Interaction) -> float:
        """Assess user's understanding level"""
        score = 0.0
        if interaction.response:
            if len(interaction.message) > 50:
                score += 0.3
            if '?' in interaction.message:
                score += 0.2
            if len(self._identify_sales_techniques(interaction.response)) > 0:
                score += 0.5
        return min(score, 1.0)
    def _contains_question(self, message: str) -> bool:
       """Check if message contains questions"""
       return '?' in message

    def _categorize_topic(self, message: str) -> str:
        """Categorize the topic of discussion"""

        # Simple keyword-based categorization
        keywords = {
            'pricing': ['price', 'cost', 'budget', 'expensive', 'cheap'],
            'product': ['product', 'feature', 'specification', 'works'],
            'objection': ['worried', 'concern', 'problem', 'issue'],
            'closing': ['buy', 'purchase', 'deal', 'contract']
        }
        
        message = message.lower()
        for category, words in keywords.items():
            if any(word in message for word in words):
                return category
        return 'general'

    def _identify_sales_techniques(self, response: Optional[str]) -> List[str]:
        """Identify sales techniques used in response"""
        techniques = []
        # Check if response exists and is not None
        if response and isinstance(response, str):
            response_text = response.lower()
            if '?' in response_text:
                techniques.append('questioning')
            if any(word in response_text for word in ['benefit', 'value']):
                techniques.append('value_selling')
            if any(word in response_text for word in ['understand', 'tell me more']):
                techniques.append('active_listening')
            if any(word in response_text for word in ['example', 'instance']):
                techniques.append('storytelling')
        return techniques

    def _identify_objections(self, message: Optional[str]) -> List[str]:
        """Identify any objections in the message"""
        objections = []
        # Check if message exists and is a string
        if message and isinstance(message, str):
            message_text = message.lower()
            if any(word in message_text for word in ['expensive', 'cost', 'price']):
                objections.append('pricing')
            if any(word in message_text for word in ['time', 'waiting', 'long']):
                objections.append('timing')
            if any(word in message_text for word in ['competition', 'competitor']):
                objections.append('competition')
        return objections

    def _assess_understanding(self, interaction: Interaction) -> float:
        """Assess user's understanding level"""
        # Simple scoring based on interaction patterns
        score = 0.0
        if interaction.response:
            # Add points for engagement indicators
            if len(interaction.message) > 50:
                score += 0.3
            if '?' in interaction.message:
                score += 0.2
            if len(self._identify_sales_techniques(interaction.response)) > 0:
                score += 0.5
        return min(score, 1.0)  # Return score between 0 and 1

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
