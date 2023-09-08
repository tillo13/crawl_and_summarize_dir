import os
import re
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
TREE_TO_WALK = os.getenv("TREE_TO_WALK")

start_time = time.time()
# Set a counter for chatgpt_prompt.txt files
file_count = 0

# Generate a unique timestamp prefix for each run
CURRENT_TIME_STAMP = datetime.now().strftime('%Y%m%d_%I%M%p')  # e.g., '20230908_1001AM'
# Define path to logs directory
logs_folder = os.path.join(os.getcwd(), 'logs')   # New line. os.getcwd() gets current working directory.

DIRECTORY_LOG_FILE = f"{logs_folder}/{CURRENT_TIME_STAMP}_processed_directories.txt" 

EXCLUDE_DIRS = [".git", ".svn", ".idea"] 
processed_directories = []

def get_newest_oldest_files(directory):
    files = []
    print(f"Processing directory: {directory}") 
    for f in os.listdir(directory):
        full_path = os.path.join(directory, f)
        print(f"Checking file: {full_path}") 
        if os.path.isfile(full_path) and not f.endswith(".env"):
            files.append(full_path)
    
    if not files:
        print(f"No valid files in directory: {directory}") 
        return None, None
        
    newest_file = max(files, key=os.path.getmtime)
    oldest_file = min(files, key=os.path.getmtime)
    return newest_file, oldest_file

def get_language_comment_pattern(filename):
    _, ext = os.path.splitext(filename)
    languages = {
        '.py': ('python', r'#(.*)'),  # Single line Python comments
    }  # removed other languages for clarity
    
    return languages.get(ext, (None, None))

def extract_comments(filename, comment_pattern):
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        comments = re.findall(comment_pattern, contents)
        return [comment.strip() for comment in comments]
    except Exception as e:
        print(f"Failed to extract comments from {filename}: {e}")
        return []
    
def contains_source_code(directory):
    source_code_exts = ['.py', '.js', '.c', '.cpp', '.java', '.rb', '.go', '.php']
    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in source_code_exts):
            return True
    return False

def contains_commented_code(filename, comment_pattern):
    comments = extract_comments(filename, comment_pattern)
    return len(comments) > 0

def process_directory(directory):
    if not contains_source_code(directory):   # Skip if no source code files found
        return

    newest_file, oldest_file = get_newest_oldest_files(directory)
    
    if newest_file is None:
       return
    
    language, comment_pattern = get_language_comment_pattern(newest_file)

    # Skip if no comments found in the newest source code file
    if comment_pattern and not contains_commented_code(newest_file, comment_pattern):  
        return
    
    newest_comments = extract_comments(newest_file, comment_pattern)[:10] if comment_pattern else []
    
    try:
        global file_count  # Declare file_count as a global variable

        with open(os.path.join(directory, 'chatgpt_prompt.txt'), 'w') as f:
            f.write(f'The newest file was created on {datetime.fromtimestamp(os.path.getmtime(newest_file)).strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'The newest file is titled {os.path.basename(newest_file)}\n')
            f.write(f'The oldest file was created on {datetime.fromtimestamp(os.path.getmtime(oldest_file)).strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'The oldest file is titled {os.path.basename(oldest_file)}\n')
            f.write(f'This directory structure appears to be: {language}\n')
            f.write(f'It has {len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name)) and not name.endswith(".env")])} files in it.\n')
            f.write(f'Here are up to 10 comments pulled from the newest file:\n')
            if newest_comments:
                f.write('\n'.join(newest_comments))
            else:
                f.write('No comments found in the newest Python file.')
        
        print(f"Processed directory {directory} successfully")
        processed_directories.append(os.path.join(directory, 'chatgpt_prompt.txt'))  

        # Increment the counter here, after the 'chatgpt_prompt.txt' file has been successfully created.
        file_count += 1 
    except Exception as e:
        print(f"Failed to process directory {directory}: {e}")

count = 0  # Counter for sucessfully processed directories
failure_count = 0  # Counter for failed directory processing

for root, dirs, files in os.walk(TREE_TO_WALK):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    try:
        process_directory(root)
        count+=1
    except Exception as e:
        print(f"Failed to process directory {root}: {e}")
        failure_count+=1

# Make sure your /logs directory exists. If not, create it
if not os.path.exists(logs_folder):  # Updated to use the logs_folder path
    os.makedirs(logs_folder)

# Write out processed directories using the timestamp-prefixed filename
with open(DIRECTORY_LOG_FILE, 'w') as f:
    for directory in processed_directories:
        f.write(directory + '\n')

# Get the time difference
elapsed_time = time.time() - start_time 

print(f"Done!\nScanned: {TREE_TO_WALK}.\nProcessed {count} directories successfully.\nEncountered {failure_count} failures.\nCreated {file_count} 'chatgpt_prompt.txt' files.\nThe script took {elapsed_time} seconds to run.")
