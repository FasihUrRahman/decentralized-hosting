# client_node/main_api.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import json
import hashlib # <-- NEW IMPORT

from .utils import shard_handler
from .network import peer_client
from .config import Config

app = FastAPI()
config = Config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

METADATA_DIR = "file_metadata"
TEMP_UPLOAD_DIR = "temp_uploads"
TEMP_RECONSTRUCT_DIR = "temp_reconstruction"
os.makedirs(METADATA_DIR, exist_ok=True)
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_RECONSTRUCT_DIR, exist_ok=True)

REGISTRY_HOST = config.REGISTRY_HOST
REGISTRY_PORT = config.REGISTRY_PORT

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    temp_upload_shard_dir = os.path.join(TEMP_UPLOAD_DIR, file.filename + "_shards")
    os.makedirs(temp_upload_shard_dir, exist_ok=True)
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # --- NEW: Generate a unique ID from the file's content ---
        file_hash = hashlib.sha256()
        with open(temp_file_path, "rb") as f:
            while chunk := f.read(4096):
                file_hash.update(chunk)
        file_id = file_hash.hexdigest()
        print(f"📄 Received file '{file.filename}', generated unique ID: {file_id}")
        
        peers = peer_client.get_peers_from_registry(REGISTRY_HOST, REGISTRY_PORT)
        peer_urls = [f"http://{p}" for p in peers]
        if not peer_urls:
            raise HTTPException(status_code=503, detail="No active peers available in the network.")
        
        manifest_path = shard_handler.process_file_to_shards(temp_file_path, temp_upload_shard_dir)
        shard_map_path = shard_handler.distribute_shards_to_peers(
            manifest_path=manifest_path,
            shard_dir=temp_upload_shard_dir,
            peer_urls=peer_urls,
            api_key=config.SECRET_KEY,
            replicas=2
        )
        
        # --- MODIFIED: Save metadata using the unique file_id ---
        final_manifest_path = os.path.join(METADATA_DIR, f"{file_id}.manifest.json")
        final_shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")
        shutil.copy(manifest_path, final_manifest_path)
        shutil.copy(shard_map_path, final_shard_map_path)
        
        with open(final_manifest_path, 'r') as f:
            manifest_content = json.load(f)
        
        print("✅ File upload process complete.")
        return {
            "message": f"File '{file.filename}' uploaded successfully.",
            "original_filename": file.filename,
            "file_id": file_id, # Return the new ID to the frontend
            "manifest": manifest_content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_upload_shard_dir):
            shutil.rmtree(temp_upload_shard_dir)
        print("🧹 Cleaned up temporary files.")


# --- MODIFIED: Download by unique file_id, not filename ---
@app.get("/download/{file_id}")
async def download_file(file_id: str):
    manifest_path = os.path.join(METADATA_DIR, f"{file_id}.manifest.json")
    shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")

    if not os.path.exists(manifest_path) or not os.path.exists(shard_map_path):
        raise HTTPException(status_code=404, detail="File with this ID not found.")
        
    # Get the original filename from the manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    original_filename = manifest.get('original_file', 'downloaded_file')
    
    output_file_path = os.path.join(TEMP_RECONSTRUCT_DIR, original_filename)

    try:
        reconstructed_file = shard_handler.reconstruct_from_peers(
            manifest_path=manifest_path,
            shard_map_path=shard_map_path,
            output_file=output_file_path,
            api_key=config.SECRET_KEY
        )
        return FileResponse(path=reconstructed_file, media_type='application/octet-stream', filename=original_filename)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not reconstruct file: {str(e)}")