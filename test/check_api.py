from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Try a simple API call
try:
    models = client.models.list()
    print(f"Success! Found {len(models.data)} models.")
    
    # Test assistant access
    assistant_id = os.getenv("ASSISTANT_ID")
    print(f"Testing access to assistant {assistant_id}")
    
    try:
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
        print(f"Success! Retrieved assistant: {assistant.name}")
    except Exception as e:
        print(f"Error accessing assistant: {str(e)}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    