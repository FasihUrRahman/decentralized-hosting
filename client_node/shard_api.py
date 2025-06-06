# client_node/shard_api.py

from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
import os
# Corrected imports with a leading dot (.)
from .utils.crypto import decrypt_data
from .config import Config

# --- Security Setup ---
config = Config()
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY")

async def get_api_key(api_key: str = Depends(API_KEY_HEADER)):
    """Dependency to validate the API key in the request header."""
    if api_key != config.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key
# --- End of Setup ---


app = FastAPI()
STORAGE_DIR = "stored_shards"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.post("/store-shard/", dependencies=[Depends(get_api_key)])
async def store_shard(index: int = Form(...), shard: UploadFile = Form(...)):
    content = await shard.read()
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    with open(file_location, "wb") as f:
        f.write(content)
    return {"status": "success", "index": index, "size": len(content)}

@app.get("/get-shard/{index}", dependencies=[Depends(get_api_key)])
def get_shard(index: int):
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    if not os.path.exists(file_location):
        return {"error": "Shard not found"}, 404

    with open(file_location, "rb") as f:
        encrypted_content = f.read()

    return StreamingResponse(iter([encrypted_content]), media_type="application/octet-stream")