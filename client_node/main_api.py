# client_node/main_api.py

from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
import json

# Use relative imports for our own modules
from .utils import shard_handler
from .network import peer_client
from .config import Config

app = FastAPI()
config = Config()

# Define temporary directories
TEMP_UPLOAD_DIR = "temp_uploads"
TEMP_SHARD_DIR = "temp_shards_for_upload"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_SHARD_DIR, exist_ok=True)

REGISTRY_HOST = config.REGISTRY_HOST
REGISTRY_PORT = config.REGISTRY_PORT


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    This endpoint orchestrates the entire file upload process.
    """
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        # 1. Save the uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"📄 Received file '{file.filename}', saved to temp location.")

        # 2. Get the list of active peers from the registry
        print(f"📡 Contacting registry at {REGISTRY_HOST}:{REGISTRY_PORT} to get peer list...")
        peers = peer_client.get_peers_from_registry(REGISTRY_HOST, REGISTRY_PORT)
        
        # Add "http://" prefix to peer addresses
        peer_urls = [f"http://{p}" for p in peers]
        
        if not peer_urls:
            raise HTTPException(status_code=503, detail="No active peers available in the network.")
        print(f"Found {len(peer_urls)} active peer(s): {peer_urls}")
        
        # 3. Process the file into encrypted shards
        print("⚙️ Processing file into encrypted shards...")
        manifest_path = shard_handler.process_file_to_shards(temp_file_path, TEMP_SHARD_DIR)

        # 4. Distribute the shards to the peer network
        print("🚀 Distributing shards to the peer network...")
        shard_map_path = shard_handler.distribute_shards_to_peers(
            manifest_path=manifest_path,
            shard_dir=TEMP_SHARD_DIR,
            peer_urls=peer_urls,
            api_key=config.SECRET_KEY,
            replicas=2  # You can make this configurable
        )
        
        # 5. Read manifest and shard map to return to the user
        with open(manifest_path, 'r') as f:
            manifest_content = json.load(f)
        with open(shard_map_path, 'r') as f:
            shard_map_content = json.load(f)

        print("✅ File upload process complete.")
        return {
            "message": f"File '{file.filename}' uploaded and distributed successfully.",
            "manifest": manifest_content,
            "shard_map": shard_map_content
        }

    except Exception as e:
        # Raise a generic server error if anything goes wrong
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        # 6. Clean up temporary files and folders
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(TEMP_SHARD_DIR):
            shutil.rmtree(TEMP_SHARD_DIR)
        print("🧹 Cleaned up temporary files.")