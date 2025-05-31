# main API file (e.g., shard_api.py)

from fastapi import FastAPI, UploadFile, Form
import os
from utils.crypto import encrypt_data, decrypt_data  # Using your provided encryption logic

app = FastAPI()
STORAGE_DIR = "stored_shards"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.post("/store-shard/")
async def store_shard(index: int = Form(...), shard: UploadFile = Form(...)):
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    
    # Read file content
    content = await shard.read()
    
    # Encrypt using your utility
    encrypted_content = encrypt_data(content)
    
    # Store encrypted shard
    with open(file_location, "wb") as f:
        f.write(encrypted_content)
    
    return {"status": "success", "index": index}

@app.get("/get-shard/{index}")
def get_shard(index: int):
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    
    if not os.path.exists(file_location):
        return {"error": "Shard not found"}
    
    with open(file_location, "rb") as f:
        encrypted_content = f.read()

    try:
        decrypted_content = decrypt_data(encrypted_content)
    except Exception as e:
        return {"error": f"Decryption failed: {str(e)}"}

    return StreamingResponse(iter([decrypted_content]), media_type="application/octet-stream")