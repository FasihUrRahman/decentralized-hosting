# client_node/test_reconstruction.py

from utils.shard_handler import (
    process_file_to_shards,
    distribute_shards_to_peers,
    reconstruct_from_peers
)
import os
import shutil

# --- CONFIGURATION ---
INPUT_FILE = "my_large_test_file.txt"
SHARD_FOLDER = "temp_shards"
RECONSTRUCTED_FILE = "reconstructed_from_peers.txt"

# IMPORTANT: Make sure your FastAPI servers are running on these addresses.
# You can run multiple instances on different ports for testing.
# Example: `uvicorn shard_api:app --host 0.0.0.0 --port 8000`
#          `uvicorn shard_api:app --host 0.0.0.0 --port 8001`
PEER_SERVERS = [
    "http://localhost:8000",
    "http://localhost:8001",
    # "http://localhost:8002", # Add more if you run more servers
]

REPLICAS = 2 # Store each shard on 2 different peers

def cleanup():
    """Removes files and folders created during the test."""
    print("\n🧹 Cleaning up generated files...")
    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)
    if os.path.exists(RECONSTRUCTED_FILE):
        os.remove(RECONSTRUCTED_FILE)
    if os.path.exists(SHARD_FOLDER):
        shutil.rmtree(SHARD_FOLDER)
    if os.path.exists("shard_map.json"):
        os.remove("shard_map.json")
    print("✨ Cleanup complete.")

def run_test():
    """Executes the full test cycle."""
    print("--- 🚀 Starting End-to-End Reconstruction Test ---")

    # 1. Create a dummy file to shard
    print(f"\n[STEP 1] Creating a test file: '{INPUT_FILE}'...")
    with open(INPUT_FILE, "w") as f:
        f.write("This is line 1.\n")
        f.write("This is a much longer line to ensure the file has some content that will be split across shards if necessary.\n")
        f.write("Decentralized storage is the future!\n" * 50) # Make it a bit larger
        f.write("This is the final line.\n")
    print("✅ Test file created.")

    # 2. Process the file into encrypted shards and create a manifest
    print(f"\n[STEP 2] Splitting '{INPUT_FILE}' into encrypted shards...")
    manifest_path = process_file_to_shards(INPUT_FILE, SHARD_FOLDER)
    print(f"✅ Manifest created at: {manifest_path}")

    # 3. Distribute these shards to the network of peers
    print(f"\n[STEP 3] Distributing shards to {len(PEER_SERVERS)} peers with {REPLICAS} replicas each...")
    shard_map_path = distribute_shards_to_peers(manifest_path, SHARD_FOLDER, PEER_SERVERS, REPLICAS)
    print(f"✅ Shard distribution complete. Map saved to: {shard_map_path}")

    # 4. Reconstruct the file by downloading shards from peers
    print(f"\n[STEP 4] Reconstructing file from peers into '{RECONSTRUCTED_FILE}'...")
    reconstruct_from_peers(manifest_path, shard_map_path, RECONSTRUCTED_FILE)
    print(f"✅ File reconstruction process finished.")

    # 5. Verification
    print("\n[STEP 5] Verifying file integrity...")
    with open(INPUT_FILE, 'r') as f1, open(RECONSTRUCTED_FILE, 'r') as f2:
        original_content = f1.read()
        reconstructed_content = f2.read()

        if original_content == reconstructed_content:
            print("✅ SUCCESS: Reconstructed file matches the original exactly!")
        else:
            print("❌ FAILURE: Reconstructed file does NOT match the original.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n--- ❌ An error occurred during the test ---")
        print(e)
    finally:
        cleanup()