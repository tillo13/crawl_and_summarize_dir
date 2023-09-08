import os
import re
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
TREE_TO_WALK = os.getenv("TREE_TO_WALK")

start_time = time.time()
file_count = 0

CURRENT_TIME_STAMP = datetime.now().strftime('%Y%m%d_%I%M%p')  
logs_folder = os.path.join(os.getcwd(), 'logs')   

DIRECTORY_LOG_FILE = f"{logs_folder}/{CURRENT_TIME_STAMP}_processed_directories.txt" 

EXCLUDE_DIRS = [".git", ".svn", ".idea"] 
processed_directories = []

def get_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and not f.endswith(".env")]

def get_language_comment_pattern(filename):
    _, ext = os.path.splitext(filename)
    languages = {'.py': ('python', r'#(.*)'),}  # removed others for clarity
    return languages.get(ext, (None, None))

def extract_comments_and_defs(filename, comment_pattern, def_pattern):
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        comments = re.findall(comment_pattern, contents)
        defs = re.findall(def_pattern, contents)
        return [comment.strip() for comment in comments], [def_.strip() for def_ in defs]
    except Exception as e:
        print(f"Failed to extract comments and functions from {filename}: {e}")
        return [], []

def contains_source_code(directory):
    source_code_exts = ['.py', '.js', '.c', '.cpp', '.java', '.rb', '.go', '.php']
    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in source_code_exts):
            return True
    return False

def get_newest_oldest_files(directory):
    files = get_files(directory)
    newest_file = max(files, key=os.path.getmtime)
    oldest_file = min(files, key=os.path.getmtime)
    return newest_file, oldest_file

def create_directory_structure(directory):
    directory_structure = ""
    for name in os.listdir(directory):
        if name not in EXCLUDE_DIRS:
            path = os.path.join(directory, name)
            if os.path.isdir(path):
                directory_structure += f"[Folder] {name}\n"
            else:
                directory_structure += f"[File] -> {name}\n"
    return directory_structure

def process_directory(directory):
    if ".git" not in os.listdir(directory):
        return 
    if not contains_source_code(directory):
        return

    python_files = [file for file in get_files(directory) if file.endswith('.py')]
    if not python_files:
        return

    all_comments = []
    all_defs = []  # Declaration of all_defs
    for file in python_files:
        language, comment_pattern = get_language_comment_pattern(file)
        if comment_pattern is None:  
            continue
            
        comment_pattern = r'#(.*)'
        def_pattern = r'def (\w+)\(.*\):'
        comments, defs = extract_comments_and_defs(file, comment_pattern, def_pattern)
        all_comments.extend(comments)
        all_defs.extend(defs[:])  # lets pull the last 20 function definitions for brevity

    newest_file, oldest_file = get_newest_oldest_files(directory)
    directory_structure = create_directory_structure(directory)
    write_prompt(all_comments[:100], all_defs, directory, language, newest_file, oldest_file, directory_structure)        

def write_prompt(comments, defs, directory, language, newest_file, oldest_file, directory_structure):
    try:
        global file_count  # Declare file_count as a global variable

        with open(os.path.join(directory, 'chatgpt_prompt.txt'), 'w') as f:
            f.write(f'The newest file was created on {datetime.fromtimestamp(os.path.getmtime(newest_file)).strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'The newest file is titled {os.path.basename(newest_file)}\n')
            f.write(f'The oldest file was created on {datetime.fromtimestamp(os.path.getmtime(oldest_file)).strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'The oldest file is titled {os.path.basename(oldest_file)}\n')
            f.write(f'This directory structure appears to be: {language}\n')
            f.write(f'It has {len(get_files(directory))} files in it.\n')
            f.write(f'### Here are up to 100 comments pulled from the Python files:\n')
            if comments:
                f.write('\n'.join(comments))
            else:
                f.write('No comments found in any Python files.')
            f.write(f'\n### Here are up to 20 function definitions pulled from the Python files:\n')
            if defs:
                f.write('\n'.join(defs))
            else:
                f.write('No function definitions found in any Python files.')
            f.write(f'### Here is the root directory structure:\n')
            f.write(directory_structure + '\n')
        
        print(f"Processed directory {directory} successfully.")
        processed_directories.append(os.path.join(directory, 'chatgpt_prompt.txt'))  
        file_count += 1 
    except Exception as e:
        print(f"Failed to process directory {directory}: {e}")

count = 0  
failure_count = 0  

for root, dirs, files in os.walk(TREE_TO_WALK):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d != 'node_modules']
    try:
        process_directory(root)
        count+=1
    except Exception as e:
        print(f"Failed to process directory {root}: {e}")
        failure_count+=1

if not os.path.exists(logs_folder):  # Updated to use the logs_folder path
    os.makedirs(logs_folder)

with open(DIRECTORY_LOG_FILE, 'w') as f:
    for directory in processed_directories:
        f.write(directory + '\n')

elapsed_time = time.time() - start_time 

print(f"Done!\nScanned: {TREE_TO_WALK}.\nProcessed {count} directories successfully.\nEncountered {failure_count} failures.\nCreated {file_count} 'chatgpt_prompt.txt' files.\nThe script took {elapsed_time} seconds to run.")