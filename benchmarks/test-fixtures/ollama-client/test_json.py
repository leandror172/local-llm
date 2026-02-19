import sys, json
sys.path.insert(0, '/mnt/i/workspaces/llm/personas')
from lib.ollama_client import ollama_chat
schema = {'type': 'object', 'properties': {'answer': {'type': 'string'}}, 'required': ['answer']}
r = ollama_chat('What color is the sky?', model='my-coder-q3', format_schema=schema)
parsed = json.loads(r['content'])
print('HAS_ANSWER:', 'answer' in parsed)
