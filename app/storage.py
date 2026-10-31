import json

def encode_tasks(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)

def decode_tasks(text):
    return json.loads(text)
