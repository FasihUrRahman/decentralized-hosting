# client_node/main_api.py

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import shutil
import os
import json
import hashlib
import requests

from .utils import shard_handler
from .network import peer_client
from .config import Config
from .database import database as db_logic
from .auth.router import router as auth_router
from .auth.security import get_current_user
from .database.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    db_logic.create_db_and_tables()
    print("🚀 Application startup: Main API is running and database is ready.")
    yield
    # Code below yield runs on shutdown
    print("🌙 Application shutdown.")

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
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

# --- Helper function for background deletion ---
def task_delete_shards_from_peers(shards_to_delete: dict, api_key: str):
    headers = {"X-API-KEY": api_key}
    for shard_name, peer_urls in shards_to_delete.items():
        for peer_url in peer_urls:
            try:
                print(f"🗑️ Asking peer {peer_url} to delete shard {shard_name}...")
                requests.delete(f"{peer_url}/delete-shard/{shard_name}", headers=headers, timeout=5)
            except Exception as e:
                print(f"Failed to request deletion of {shard_name} from {peer_url}: {e}")

# --- MODIFIED: Endpoints now require authentication ---

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # ... (function logic remains the same)
    temp_upload_shard_dir = os.path.join(TEMP_UPLOAD_DIR, file.filename + "_shards")
    os.makedirs(temp_upload_shard_dir, exist_ok=True)
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
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
        final_manifest_path = os.path.join(METADATA_DIR, f"{file_id}.manifest.json")
        final_shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")
        shutil.copy(manifest_path, final_manifest_path)
        shutil.copy(shard_map_path, final_shard_map_path)
        with open(final_manifest_path, 'r') as f:
            manifest_content = json.load(f)
        return {
            "message": f"File '{file.filename}' uploaded successfully.",
            "original_filename": file.filename,
            "file_id": file_id,
            "manifest": manifest_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_upload_shard_dir):
            shutil.rmtree(temp_upload_shard_dir)

@app.get("/download/{file_id}")
async def download_file(
    file_id: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # ... (function logic remains the same)
    manifest_path = os.path.join(METADATA_DIR, f"{file_id}.manifest.json")
    shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")
    if not os.path.exists(manifest_path) or not os.path.exists(shard_map_path):
        raise HTTPException(status_code=404, detail="File with this ID not found.")
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
        background_tasks.add_task(os.remove, reconstructed_file)
        return FileResponse(path=reconstructed_file, media_type='application/octet-stream', filename=original_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not reconstruct file: {str(e)}")

@app.delete("/delete/{file_id}")
def delete_file(
    file_id: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # ... (function logic remains the same)
    manifest_path = os.path.join(METADATA_DIR, f"{file_id}.manifest.json")
    shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")
    if not os.path.exists(manifest_path) or not os.path.exists(shard_map_path):
        raise HTTPException(status_code=404, detail="File with this ID not found.")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    with open(shard_map_path, 'r') as f:
        shard_map = json.load(f)
    shards_to_delete = {}
    for shard_info in manifest['shards']:
        shard_name = shard_info['shard']
        index_str = str(shard_info['index'])
        if index_str in shard_map:
            shards_to_delete[shard_name] = shard_map[index_str]
    background_tasks.add_task(
        task_delete_shards_from_peers,
        shards_to_delete,
        config.SECRET_KEY
    )
    os.remove(manifest_path)
    os.remove(shard_map_path)
    return {"status": "success", "detail": f"Deletion process for file ID {file_id} initiated."}

# The /network/ledger endpoint does not need to be protected
@app.get("/network/ledger", response_class=JSONResponse)
def get_ledger():
    ledger_path = os.path.join(METADATA_DIR, "ledger.json")
    if not os.path.exists(ledger_path):
        return {}
    with open(ledger_path, 'r') as f:
        try:
            ledger_data = json.load(f)
            return ledger_data
        except json.JSONDecodeError:
            return {"error": "Ledger file is corrupt or empty."}