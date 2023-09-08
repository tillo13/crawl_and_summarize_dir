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

def extract_comments_and_defs(filename, comment_pattern, def_pattern, import_pattern):  # Add import_pattern
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        comments = re.findall(comment_pattern, contents)
        defs = re.findall(def_pattern, contents)
        imports = re.findall(import_pattern, contents)  # Find all matches to import_pattern
        return [comment.strip() for comment in comments], [def_.strip() for def_ in defs], list(set(imports))  # Add imports to return statement
    except Exception as e:
        print(f"Failed to extract comments and functions from {filename}: {e}")
        return [], [], []  # Add an empty list for imports

def contains_source_code(directory):
    source_code_exts = ['.py', '.js', '.c', '.cpp', '.java', '.rb', '.go', '.php']
    for filename in os.listdir(directory):
        if any(filename.endswith(ext) for ext in source_code_exts):
            return True
    return False

def get_newest_oldest_files(directory):
    python_files = [file for file in get_files(directory) if file.endswith('.py')]
    if not python_files:
        return None, None
    
    newest_file = max(python_files, key=os.path.getmtime)
    oldest_file = min(python_files, key=os.path.getmtime)
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

def count_lines_in_file(filename):
    _, ext = os.path.splitext(filename)
    if ext == '.py':
        with open(filename, 'r') as f:
            return sum(1 for line in f)
    else:
        return None

def process_directory(directory):
    if ".git" not in os.listdir(directory):
        return 
    if not contains_source_code(directory):
        return

    python_files = [file for file in get_files(directory) if file.endswith('.py')]
    if not python_files:
        return

    all_comments = []
    all_defs = []
    all_imports = []  # Declare all_imports
    for file in python_files:
        language, comment_pattern = get_language_comment_pattern(file)
        if comment_pattern is None:  
            continue
            
        comment_pattern = r'#(.*)'
        def_pattern = r'def (\w+)\(.*\):'
        import_pattern = r'(?:import|from) (\w+)'  # Declare import_pattern
        comments, defs, imports = extract_comments_and_defs(file, comment_pattern, def_pattern, import_pattern)  # Update function call
        all_comments.extend(comments)
        all_defs.extend(defs[:]) 
        all_imports.extend(imports)  # Extend all_imports with imports from file

    newest_file, oldest_file = get_newest_oldest_files(directory)
    directory_structure = create_directory_structure(directory)
    write_prompt(all_comments[:100], all_defs, all_imports, directory, language, newest_file, oldest_file, directory_structure)  # Add all_imports to function call      

def write_prompt(comments, defs, imports, directory, language, newest_file, oldest_file, directory_structure): 
    try:
        global file_count  # Declare file_count as a global variable

        with open(os.path.join(directory, 'chatgpt_prompt.txt'), 'w') as f:
            f.write(f'### Here is the root directory structure:\n')
            f.write(directory_structure + '\n')
            newest_file_lines = count_lines_in_file(newest_file)
            oldest_file_lines = count_lines_in_file(oldest_file)            
            f.write(f'The newest file, titled "{os.path.basename(newest_file)}", was created on {datetime.fromtimestamp(os.path.getmtime(newest_file)).strftime("%Y-%m-%d %H:%M:%S")} and has {newest_file_lines} lines.\n')
            f.write(f'The oldest file, titled "{os.path.basename(oldest_file)}", was created on {datetime.fromtimestamp(os.path.getmtime(oldest_file)).strftime("%Y-%m-%d %H:%M:%S")} and has {oldest_file_lines} lines.\n')
            # write the imports blocks
            f.write(f'\n### Here are the unique imports detected in the Python files:\n')
            if imports:
                f.write('\n'.join(imports))
            else:
                f.write('No import statements found in any Python files.')
            f.write(f'\n### Here are up to 100 comments pulled from the Python files:\n')
            if comments:
                f.write('\n'.join(comments))
            else:
                f.write('No comments found in any Python files.')
            f.write(f'\n\n### Here are up to 20 function definitions pulled from the Python files:\n')
            if defs:
                f.write('\n'.join(defs))
            else:
                f.write('No function definitions found in any Python files.')
        
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