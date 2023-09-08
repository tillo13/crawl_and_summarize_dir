import os
import time
from dotenv import load_dotenv

load_dotenv()  
TREE_TO_WALK = os.getenv("TREE_TO_WALK")

count = 0

start_time = time.time()

for root, dirs, files in os.walk(TREE_TO_WALK):
    for file in files:
        if file in ['chatgpt_prompt.txt', 'chatgpt_results.json']:
            os.remove(os.path.join(root, file))
            print(f'Deleted file {os.path.join(root, file)}')
            count += 1

elapsed_time = time.time() - start_time

print(f"Done!\n{count} files deleted.\nThe script took {elapsed_time} seconds to run.")