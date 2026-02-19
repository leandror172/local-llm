import sys
sys.path.insert(0, '/mnt/i/workspaces/llm/personas')
from lib.ollama_client import ollama_chat
r = ollama_chat('Hi', model='my-coder-q3', system='You are a pirate. Reply in one sentence.')
print('CONTENT:', r['content'][:200])
