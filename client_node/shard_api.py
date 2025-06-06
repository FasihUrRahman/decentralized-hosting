# client_node/shard_api.py

import uvicorn
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse, JSONResponse
import os
import socket
from contextlib import asynccontextmanager  # <-- NEW IMPORT
from utils.crypto import decrypt_data
from config import Config

config = Config()
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY")

async def get_api_key(api_key: str = Depends(API_KEY_HEADER)):
    if api_key != config.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key")
    return api_key

# --- NEW: Lifespan event handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    print("🚀 Application startup: Registering with registry...")
    registry_host = config.REGISTRY_HOST
    registry_port = config.REGISTRY_PORT
    peer_port = config.port
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((registry_host, registry_port))
            address = f"127.0.0.1:{peer_port}"
            s.sendall(f"REGISTER {address}".encode())
            response = s.recv(1024).decode()
            print(f"✅ Registered with registry on port {peer_port}: {response}")
    except Exception as e:
        print(f"❌ Could not register with registry: {e}")
    
    yield
    # Code below yield runs on shutdown (optional)
    print("🌙 Application shutdown.")

app = FastAPI(lifespan=lifespan)  # <-- Tell FastAPI to use the new lifespan handler

@app.get("/health")
def health_check():
    """A simple endpoint for the registry to check if the peer is alive."""
    return JSONResponse(content={"status": "ok"})

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

if __name__ == "__main__":
    print(f"Starting peer node on port {config.port}...")
    uvicorn.run(app, host="0.0.0.0", port=config.port)