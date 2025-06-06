# client_node/utils/shard_handler.py

import os
import json
import hashlib
import requests
import shutil
import random
from .crypto import encrypt_data, decrypt_data

def split_file(file_path: str, shard_size: int = 1024 * 1024):
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
        shard_name = f"{sha256}.bin"
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

def distribute_shards_to_peers(manifest_path: str, shard_dir: str, peer_urls: list[str], api_key: str, replicas: int = 2, shard_map_path="shard_map.json"):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    headers = {"X-API-KEY": api_key}
    shard_map = {}

    for shard_info in manifest['shards']:
        index = shard_info['index']
        shard_name = shard_info['shard']
        shard_map[index] = []
        available_peers = random.sample(peer_urls, len(peer_urls))
        
        while len(shard_map[index]) < replicas:
            if not available_peers:
                print(f"⚠️ Warning: Ran out of peers for shard {index}. Stored {len(shard_map[index])}/{replicas} replicas.")
                break

            peer = available_peers.pop(0)
            shard_file_path = os.path.join(shard_dir, shard_name)
            
            try:
                with open(shard_file_path, 'rb') as f_shard:
                    # --- THIS IS THE FIX ---
                    # The `files` dictionary is all that's needed.
                    # The `data` dictionary containing the index has been removed.
                    files = {"shard": (shard_name, f_shard, "application/octet-stream")}
                    
                    print(f"📤 Attempting to send shard {shard_name} to {peer}...")
                    r = requests.post(f"{peer}/store-shard/", files=files, headers=headers, timeout=5)
                    r.raise_for_status()
                    
                    print(f"✅ Shard {index} successfully sent to {peer}")
                    shard_map[index].append(peer)

            except requests.RequestException as e:
                print(f"❌ Failed to send shard {index} to {peer}: {e}. Trying next peer.")

    with open(shard_map_path, "w") as f:
        json.dump(shard_map, f, indent=2)
    print(f"✅ Shard map saved to {shard_map_path}")
    return shard_map_path

# The rest of the functions remain the same...
def reconstruct_from_peers(manifest_path: str, shard_map_path: str, output_file: str, api_key: str):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    with open(shard_map_path, 'r') as f:
        shard_map = json.load(f)

    headers = {"X-API-KEY": api_key}
    print(f"🚀 Starting reconstruction of '{manifest['original_file']}'...")
    with open(output_file, 'wb') as out_file:
        for shard_info in sorted(manifest['shards'], key=lambda x: x['index']):
            index_str = str(shard_info['index'])
            shard_name = shard_info['shard']
            if index_str not in shard_map or not shard_map[index_str]:
                raise RuntimeError(f"No peers found for shard {index_str} in shard map.")
            
            peer_urls = shard_map[index_str]
            downloaded = False
            for peer_url in peer_urls:
                try:
                    print(f"📥 Attempting to download shard '{shard_name}' from {peer_url}...")
                    response = requests.get(f"{peer_url}/get-shard/{shard_name}", headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    decrypted_data = decrypt_data(response.content)
                    if hashlib.sha256(response.content).hexdigest() != shard_info['sha256']:
                         raise ValueError(f"Hash mismatch for {shard_name}")

                    out_file.write(decrypted_data)
                    print(f"✅ Successfully downloaded and processed shard {shard_name}.")
                    downloaded = True
                    break 
                except Exception as e:
                    print(f"⚠️ Could not fetch or process shard {shard_name} from {peer_url}: {e}")
            
            if not downloaded:
                raise ConnectionError(f"Failed to download shard {shard_name} from any available peers.")

    print(f"✅ File reconstructed successfully at: {output_file}")
    return output_file