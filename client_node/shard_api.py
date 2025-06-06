# client_node/shard_api.py

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
import os
from utils.crypto import decrypt_data, encrypt_data

app = FastAPI()
STORAGE_DIR = "stored_shards"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.post("/store-shard/")
async def store_shard(index: int = Form(...), shard: UploadFile = Form(...)):
    # The file content from the form is already the raw binary of the shard
    content = await shard.read()

    # Per the project design, shards are encrypted *before* distribution.
    # The server just stores the encrypted blob it receives.
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    with open(file_location, "wb") as f:
        f.write(content)

    return {"status": "success", "index": index, "size": len(content)}

@app.get("/get-shard/{index}")
def get_shard(index: int):
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")

    if not os.path.exists(file_location):
        return {"error": "Shard not found"}, 404

    with open(file_location, "rb") as f:
        encrypted_content = f.read()

    # The server returns the encrypted content.
    # Decryption happens on the client side after reconstruction.
    return StreamingResponse(iter([encrypted_content]), media_type="application/octet-stream")