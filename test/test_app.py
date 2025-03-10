from flask import Flask, jsonify
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <body>
        <h1>MAI Test App</h1>
        <p>This is a test deployment.</p>
        <p><a href="/debug">Check debug info</a></p>
    </body>
    </html>
    """

@app.route('/debug')
def debug():
    """Debug endpoint to test basic functionality"""
    debug_info = {
        'app': 'running',
        'environment_vars': {
            'OPENAI_API_KEY': 'present' if os.getenv('OPENAI_API_KEY') else 'missing',
            'ASSISTANT_ID': 'present' if os.getenv('ASSISTANT_ID') else 'missing',
        }
    }
    
    # Only test OpenAI if we have the API key
    if os.getenv('OPENAI_API_KEY'):
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            models = client.models.list()
            debug_info['openai_api'] = f"Connected (found {len(models.data)} models)"
            
            # Test Assistant ID if we have it
            if os.getenv('ASSISTANT_ID'):
                try:
                    assistant = client.beta.assistants.retrieve(
                        assistant_id=os.getenv('ASSISTANT_ID')
                    )
                    debug_info['assistant'] = f"Found: {assistant.name}"
                except Exception as e:
                    debug_info['assistant_error'] = str(e)
        except Exception as e:
            debug_info['openai_error'] = str(e)
    
    return jsonify(debug_info)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    