import json
from typing import List
from server import Server
from typing import Dict

def serialize(command: Dict) -> str:
    return json.dumps(command)

def deserialize(json_str: str) -> Dict:
    if str == '':
        return {}
    return json.loads(json_str)