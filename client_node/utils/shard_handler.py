# utils/shard_handler.py

import os
import json
import hashlib
import requests
import shutil
from utils.crypto import encrypt_data, decrypt_data
import random

def split_file(file_path: str, shard_size: int = 1024 * 1024):  # 1MB
    with open(file_path, 'rb') as f:
        index = 0
        while chunk := f.read(shard_size):
            yield index, chunk
            index += 1

def process_file_to_shards(file_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    manifest = {
        'original_file': os.path.basename(file_path),
        'shards': []
    }

    for index, chunk in split_file(file_path):
        encrypted = encrypt_data(chunk)
        sha256 = hashlib.sha256(encrypted).hexdigest()
        shard_name = f'shard_{index}.bin'
        shard_path = os.path.join(output_dir, shard_name)

        with open(shard_path, 'wb') as f:
            f.write(encrypted)

        manifest['shards'].append({
            'index': index,
            'shard': shard_name,
            'sha256': sha256
        })

    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ File split and encrypted into {len(manifest['shards'])} shards.")
    return manifest_path

def reconstruct_file_from_shards(manifest_path: str, shard_dir: str, output_file: str):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    with open(output_file, 'wb') as out:
        for shard_info in sorted(manifest['shards'], key=lambda x: x['index']):
            shard_file = os.path.join(shard_dir, shard_info['shard'])

            if not os.path.exists(shard_file):
                raise FileNotFoundError(f"Missing shard file: {shard_info['shard']}")

            with open(shard_file, 'rb') as f:
                encrypted = f.read()

            # Integrity check
            if hashlib.sha256(encrypted).hexdigest() != shard_info['sha256']:
                raise ValueError(f"Hash mismatch for {shard_info['shard']}")

            decrypted = decrypt_data(encrypted)
            out.write(decrypted)

    print(f"✅ File reconstructed successfully at: {output_file}")

def distribute_shards_to_peers(manifest_path: str, shard_dir: str, peer_urls: list[str], replicas: int = 2, shard_map_path="shard_map.json"):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    if len(peer_urls) < replicas:
        raise ValueError(f"Not enough peers available ({len(peer_urls)}) to meet replica requirement ({replicas})")

    shard_map = {}

    for shard_info in manifest['shards']:
        # Select random unique peers for each shard
        selected_peers = random.sample(peer_urls, replicas)
        shard_map[shard_info['index']] = []
        shard_file_path = os.path.join(shard_dir, shard_info['shard'])

        with open(shard_file_path, 'rb') as f:
            files = {
                "shard": (shard_info['shard'], f, "application/octet-stream")
            }
            data = {
                "index": shard_info['index']
            }
            
            for peer in selected_peers:
                try:
                    # Reset file read pointer for each upload
                    f.seek(0)
                    r = requests.post(f"{peer}/store-shard/", files=files, data=data, timeout=10)
                    r.raise_for_status() # Raises an exception for bad status codes
                    
                    print(f"📤 Shard {shard_info['index']} sent to {peer}")
                    shard_map[shard_info['index']].append(peer)

                except requests.RequestException as e:
                    print(f"❌ Failed to send shard {shard_info['index']} to {peer}: {e}")

    with open(shard_map_path, "w") as f:
        json.dump(shard_map, f, indent=2)
    
    print(f"✅ Shard map with {replicas} replicas per shard saved to {shard_map_path}")
    return shard_map_path


# --- NEW FUNCTIONALITY ---

def reconstruct_from_peers(manifest_path: str, shard_map_path: str, output_file: str):
    """
    Downloads shards from peers listed in the shard map and reconstructs the original file.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    if not os.path.exists(shard_map_path):
        raise FileNotFoundError(f"Shard map file not found: {shard_map_path}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    with open(shard_map_path, 'r') as f:
        shard_map = json.load(f)

    # Create a temporary directory to download shards
    temp_shard_dir = "downloaded_shards"
    if os.path.exists(temp_shard_dir):
        shutil.rmtree(temp_shard_dir)
    os.makedirs(temp_shard_dir)

    print(f"🚀 Starting reconstruction of '{manifest['original_file']}'...")

    for shard_info in manifest['shards']:
        index_str = str(shard_info['index'])
        
        if index_str not in shard_map or not shard_map[index_str]:
            raise RuntimeError(f"No peers found for shard {index_str} in shard map.")

        peer_urls = shard_map[index_str]
        
        # Try to download from listed peers until one succeeds
        downloaded = False
        for peer_url in peer_urls:
            try:
                print(f"📥 Attempting to download shard {index_str} from {peer_url}...")
                response = requests.get(f"{peer_url}/get-shard/{index_str}", timeout=10)
                response.raise_for_status()
                
                # Save the downloaded shard
                shard_path = os.path.join(temp_shard_dir, shard_info['shard'])
                with open(shard_path, 'wb') as f:
                    f.write(response.content)

                print(f"✅ Successfully downloaded shard {index_str}.")
                downloaded = True
                break # Move to the next shard
            except requests.RequestException as e:
                print(f"⚠️ Could not fetch shard {index_str} from {peer_url}: {e}")
        
        if not downloaded:
            shutil.rmtree(temp_shard_dir) # Clean up
            raise ConnectionError(f"Failed to download shard {index_str} from any of the available peers.")

    # Once all shards are downloaded, reconstruct the file
    try:
        reconstruct_file_from_shards(manifest_path, temp_shard_dir, output_file)
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_shard_dir)