# shared.py
import json
import pathlib

DATA_FILE = pathlib.Path("data/reaction_roles.json")

def save_role_data(reaction_role_mapping):
    with open(DATA_FILE, 'w') as f:
        json.dump(reaction_role_mapping, f, indent=4)

def load_role_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

reaction_role_mapping = load_role_data()