import json

def object_field(value):
    if isinstance(value,dict):return value
    try:
        x=json.loads(value or '{}');return x if isinstance(x,dict) else {}
    except (TypeError,ValueError):return {}

def list_field(value):
    if isinstance(value,list):return value
    try:
        x=json.loads(value or '[]');return x if isinstance(x,list) else [x]
    except (TypeError,ValueError):return []
