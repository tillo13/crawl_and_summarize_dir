import os
import json
import requests
from dotenv import load_dotenv

# Loading environment variables from .env file
load_dotenv('.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
print(OPENAI_API_KEY)
OPENAI_API_URL = f"{os.getenv('OPENAI_API_BASE_URL')}/{os.getenv('OPENAI_API_DEPLOYMENT')}?api-version={os.getenv('OPENAI_API_VERSION')}"
HEADERS = {'api-key': OPENAI_API_KEY}

data = {
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Hello, world!"
        }
    ]
}

response = requests.post(OPENAI_API_URL, headers=HEADERS, json=data)

if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2))
else:
    print("Failed to connect. Error: ", response.status_code)