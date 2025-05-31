# utils/directory.py
import json, os

DIRECTORY_FILE = "directory.json"

def save_metadata(chunk_id, filename, owner):
    directory = {}
    if os.path.exists(DIRECTORY_FILE):
        with open(DIRECTORY_FILE, "r") as f:
            directory = json.load(f)
    directory[chunk_id] = {"filename": filename, "owner": owner}
    with open(DIRECTORY_FILE, "w") as f:
        json.dump(directory, f)

def get_metadata(chunk_id):
    if os.path.exists(DIRECTORY_FILE):
        with open(DIRECTORY_FILE, "r") as f:
            directory = json.load(f)
            return directory.get(chunk_id, {})
    return {}

