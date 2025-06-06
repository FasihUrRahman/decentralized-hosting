# client_node/shard_api.py

import uvicorn
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse, JSONResponse
import os
import socket
import time
from contextlib import asynccontextmanager
from config import Config

config = Config()
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key: str = Depends(API_KEY_HEADER)):
    if not api_key or api_key != config.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Application startup on port {config.port}: Registering with registry...")
    registry_host = config.REGISTRY_HOST
    registry_port = config.REGISTRY_PORT
    peer_port = config.port
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((registry_host, registry_port))
                address = f"{config.PEER_HOSTNAME}:{peer_port}"
                s.sendall(f"REGISTER {address}".encode())
                response = s.recv(1024).decode()
                print(f"✅ Registered with registry as '{address}': {response}")
                break
        except ConnectionRefusedError:
            print(f"Registry connection refused. Retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2)
    else:
        print(f"❌ Could not register with registry after several attempts.")
    
    yield
    print("🌙 Application shutdown.")


app = FastAPI(lifespan=lifespan)

@app.get("/health", response_class=JSONResponse)
def health_check():
    return {"status": "ok"}

STORAGE_DIR = "stored_shards"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.post("/store-shard/", dependencies=[Depends(get_api_key)])
async def store_shard(shard: UploadFile = Form(...)):
    file_location = os.path.join(STORAGE_DIR, shard.filename)
    if os.path.exists(file_location):
        return {"status": "success", "detail": "shard already exists"}
    content = await shard.read()
    with open(file_location, "wb") as f:
        f.write(content)
    return {"status": "success", "filename": shard.filename, "size": len(content)}

@app.get("/get-shard/{shard_name}", dependencies=[Depends(get_api_key)])
def get_shard(shard_name: str):
    file_location = os.path.join(STORAGE_DIR, shard_name)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"Shard '{shard_name}' not found.")
    return FileResponse(path=file_location, media_type='application/octet-stream')

# --- NEW DELETE ENDPOINT ---
@app.delete("/delete-shard/{shard_name}", dependencies=[Depends(get_api_key)])
def delete_shard(shard_name: str):
    """
    Finds and deletes a specific shard from the peer's storage.
    """
    try:
        file_location = os.path.join(STORAGE_DIR, shard_name)
        if os.path.exists(file_location):
            os.remove(file_location)
            print(f"🗑️ Deleted shard: {shard_name}")
            return JSONResponse(content={"status": "success", "detail": f"Shard '{shard_name}' deleted."})
        else:
            print(f"ℹ️ Shard not found, but considering it deleted: {shard_name}")
            return JSONResponse(content={"status": "success", "detail": f"Shard '{shard_name}' not found."})
    except Exception as e:
        print(f"❌ Error deleting shard {shard_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not delete shard: {str(e)}")


if __name__ == "__main__":
    # Note: The 'f-string' for the app path was a bug in a previous version.
    # Uvicorn needs the import string for reloading to work, but since we are
    # not using the reloader in Docker, passing the app object directly is fine.
    uvicorn.run(app, host="0.0.0.0", port=config.port)