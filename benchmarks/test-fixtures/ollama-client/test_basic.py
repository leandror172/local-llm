import sys
sys.path.insert(0, '/mnt/i/workspaces/llm/personas')
from lib.ollama_client import ollama_chat
r = ollama_chat('What is 2+2? Reply with just the number.', model='my-coder-q3')
print('CONTENT:', r['content'][:100])
print('MODEL:', r['model'])
