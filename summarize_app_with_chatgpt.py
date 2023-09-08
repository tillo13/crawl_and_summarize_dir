import os
import requests
import json
import re
import time

from dotenv import load_dotenv
# Prepare to track processing time
start_time = time.time()

# Load environment variables
load_dotenv()

# Initialize a counter for the processed files
processed_files_count = 0
directories_to_skip = []
no_prompt_files = 0

# Get the directory to walk from the env variables
TREE_TO_WALK = os.getenv("TREE_TO_WALK")

# Define the API endpoint & headers
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HEADERS = {'api-key': OPENAI_API_KEY}

API_VERSION = os.getenv("OPENAI_API_VERSION")
BASE_URL = os.getenv("OPENAI_API_BASE_URL")
DEPLOYMENT = os.getenv("OPENAI_API_DEPLOYMENT")

OPENAI_API_URL = f"{BASE_URL}/{DEPLOYMENT}?api-version={API_VERSION}"

def remove_extra_spaces_comments(text):
    lines = text.split('\n')
    stripped = [line for line in lines if not line.strip().startswith('#')]
    clean_text = ' '.join(stripped)
    clean_text = re.sub('\s+', ' ', clean_text).strip()  
    clean_text = re.sub('\"\"\"(.*?)\"\"\"', '', clean_text, flags=re.MULTILINE|re.DOTALL) # remove multi-line comments
    clean_text = re.sub("'''(.*?)'''", '', clean_text, flags=re.MULTILINE|re.DOTALL) # remove multi-line comments
    return clean_text

max_tokens = 4096  # Maximum context length for the model

def get_token_count(text):
    return len(text.split())

def chatgpt_api_request(data):
    retry_count = 1
    retry_data = data.copy()

    while retry_count <= 10:
        try:
            print("\n--- Preparing to send request to OpenAI API ---")
            print("Using this URL: ", OPENAI_API_URL)
            print("Sending this payload: ", retry_data)

            response = requests.post(OPENAI_API_URL, headers=HEADERS, json=retry_data)
            response.raise_for_status()
            if response.status_code == 200:
                return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 400 and 'context_length_exceeded' in response.text:
                retry_data["messages"][1]["content"] = retry_data["messages"][1]["content"][:-500]
                retry_count += 1
                print(f"Attempt #{retry_count} with a size of {get_token_count(retry_data['messages'][1]['content'])} tokens.")
            else:
                print("Exception: ", e)
                print("OpenAI API request failed.")
                break
        finally:
            print("\n--- Response received from OpenAI API ---")
            print("Status code: ", response.status_code)
            print("Headers: ", response.headers)
            print("Response body: ", response.text)

        if retry_count > 10:  # Max number of retries to avoid endless loop
            print("Reached maximum number of retries.")
            break

    return None  # return None if all retry attempts failed

#deduce the files that need to be processed
for root, dirs, files in os.walk(TREE_TO_WALK):
    if 'chatgpt_results.json' in files:
        directories_to_skip.append(root)
print(f"\nWe will skip these files: {directories_to_skip}")

# Traverse through the directories
for root, dirs, files in os.walk(TREE_TO_WALK):
    if root in directories_to_skip:
            print(f"Skipping directory '{root}', 'chatgpt_results.json' already present.")
            continue
    if 'chatgpt_prompt.txt' in files:
        # Read the file content
        with open(os.path.join(root, 'chatgpt_prompt.txt'), 'r') as file:
            prompt_text = file.read()

        # Shrink the payload
        prompt_text = remove_extra_spaces_comments(prompt_text)

        # Make a request to the API

        data = {
            'messages': [
                {'role': 'system', 'content': 'Your role is to generate a detailed bulleted list summarizing the probable purpose of this app based on the information given.'},
                {'role': 'user', 'content': prompt_text}
            ]}
        
        response = chatgpt_api_request(data)

        if response:
            # Get the choice text from the completion
            summary_text = response['choices'][0]['message']['content']
            processed_files_count += 1    # Increment the processed files counter
            # Convert the response to a formatted JSON string
            json_response = json.dumps(response, indent=4)

            # Write the entire json response to a file
            with open(os.path.join(root, 'chatgpt_results.json'), 'w') as file:
                file.write(json_response)

#finish the script
start = time.time()
processed_files = 0
skipped_files = 0

# Now start your processing loop
for root, dirs, files in os.walk(TREE_TO_WALK):
    if root in directories_to_skip:
        print(f"Skipping directory '{root}', 'chatgpt_results.json' already present.")
        skipped_files += 1
        continue

    # Check if 'chatgpt_prompt.txt' is in the directory
    if 'chatgpt_prompt.txt' in files:
        print(f"Processing directory: {root}")
        # Read the file content
        with open(os.path.join(root, 'chatgpt_prompt.txt'), 'r') as file:
            prompt_text = file.read()

        # Shrink the payload
        prompt_text = remove_extra_spaces_comments(prompt_text)

        # Define the API request payload
        data = {
            'messages': [
                {'role': 'system', 'content': 'You are to generate a detailed bulleted list summarizing the probable purpose of this app based on the information given.'},
                {'role': 'user', 'content': prompt_text}
            ]}

        # Call the OpenAI API
        response = chatgpt_api_request(data)
        
        if response:
            # Get the choice text from the completion
            summary_text = response['choices'][0]['message']['content']

            # Convert the response to a formatted JSON string
            json_response = json.dumps(response, indent=4)

            # Write the entire json response to a file
            with open(os.path.join(root, 'chatgpt_results.json'), 'w') as file:
                file.write(json_response)
            
            processed_files += 1  # Increment the processed files counter
    else:
        #print(f"No 'chatgpt_prompt.txt' in directory: {root}")
        no_prompt_files += 1

# Calculate elapsed time
end_time = time.time()
elapsed_time = end_time - start_time

print(f"\nProcessed {processed_files} files.")
print(f"Skipped {skipped_files} files due to existing 'chatgpt_results.json'.")
print(f"\nTotal number of directories without 'chatgpt_prompt.txt': {no_prompt_files}")
print(f"Total processing time: {elapsed_time} seconds.")