from pymongo import MongoClient
uri = "mongodb+srv://Douglas:CodeMaster@aibotsales.trke1.mongodb.net/?retryWrites=true&w=majority&appName=AIBotSales"
client = MongoClient(uri)
try:
    response = client.admin.command('ping')
    print("Connected successfully! Response:", response)
except Exception as e:
    print(f"Error: {e}")