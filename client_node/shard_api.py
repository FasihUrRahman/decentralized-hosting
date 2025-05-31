from fastapi import FastAPI, UploadFile, Form
import os

app = FastAPI()
STORAGE_DIR = "stored_shards"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.post("/store-shard/")
async def store_shard(index: int = Form(...), shard: UploadFile = Form(...)):
    file_location = os.path.join(STORAGE_DIR, f"shard_{index}.bin")
    with open(file_location, "wb") as f:
        content = await shard.read()
        f.write(content)
    return {"status": "success", "index": index}
