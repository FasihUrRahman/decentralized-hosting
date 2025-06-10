# client_node/utils/shard_handler.py

import os
import json
import hashlib
import requests
import shutil
import random
from .crypto import encrypt_data, decrypt_data

def process_file_to_shards(file_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    manifest = {'original_file': os.path.basename(file_path), 'shards': []}
    
    with open(file_path, 'rb') as f:
        index = 0
        while chunk := f.read(1024 * 1024): # 1MB shard size
            encrypted = encrypt_data(chunk)
            sha256 = hashlib.sha256(encrypted).hexdigest()
            shard_name = f"{sha256}.bin"
            shard_path = os.path.join(output_dir, shard_name)
            
            with open(shard_path, 'wb') as f_shard:
                f_shard.write(encrypted)
            
            manifest['shards'].append({
                'index': index,
                'shard': shard_name,
                'sha256': sha256
            })
            index += 1
            
    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    return manifest_path

def distribute_shards_to_peers(manifest_path: str, shard_dir: str, peer_urls: list, api_key: str, replicas: int):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    headers = {"X-API-KEY": api_key}
    shard_map = {}
    
    for shard_info in manifest['shards']:
        shard_index_str = str(shard_info['index'])
        shard_name = shard_info['shard']
        shard_map[shard_index_str] = []
        
        peers_to_try = list(peer_urls)
        
        while len(shard_map[shard_index_str]) < replicas and peers_to_try:
            peer_url = random.choice(peers_to_try)
            peers_to_try.remove(peer_url)
            
            shard_file_path = os.path.join(shard_dir, shard_name)
            
            try:
                with open(shard_file_path, 'rb') as f_shard:
                    files = {"shard": (shard_name, f_shard, "application/octet-stream")}
                    print(f"📤 Attempting to send shard {shard_name} to {peer_url}...")
                    r = requests.post(f"{peer_url}/store-shard/", files=files, headers=headers, timeout=10)
                    r.raise_for_status()
                    shard_map[shard_index_str].append(peer_url)
                    print(f"✅ Shard {shard_name} successfully sent to {peer_url}")
            except requests.RequestException as e:
                print(f"❌ Failed to send shard {shard_name} to {peer_url}: {e}")

    shard_map_path = os.path.join(shard_dir, "shard_map.json")
    with open(shard_map_path, "w") as f:
        json.dump(shard_map, f, indent=2)
    return shard_map_path


def reconstruct_from_peers(manifest_path: str, shard_map_path: str, output_file: str, api_key: str):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    with open(shard_map_path, 'r') as f:
        shard_map = json.load(f)

    headers = {"X-API-KEY": api_key}
    
    with open(output_file, 'wb') as out_file:
        for shard_info in sorted(manifest['shards'], key=lambda x: x['index']):
            index_str = str(shard_info['index'])
            shard_name = shard_info['shard']
            expected_hash = shard_info['sha256']
            
            peers_with_shard = shard_map.get(index_str, [])
            if not peers_with_shard:
                raise ConnectionError(f"No peers found for shard {shard_name}")

            downloaded = False
            for peer_url in peers_with_shard:
                try:
                    print(f"📥 Attempting to download shard '{shard_name}' from {peer_url}...")
                    response = requests.get(f"{peer_url}/get-shard/{shard_name}", headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    encrypted_data = response.content
                    if hashlib.sha256(encrypted_data).hexdigest() != expected_hash:
                         raise ValueError(f"Hash mismatch for shard {shard_name}")

                    decrypted_data = decrypt_data(encrypted_data)
                    out_file.write(decrypted_data)
                    print(f"✅ Successfully downloaded and processed shard {shard_name}.")
                    downloaded = True
                    break
                except Exception as e:
                    print(f"⚠️ Could not fetch or process shard {shard_name} from {peer_url}: {e}")
            
            if not downloaded:
                raise ConnectionError(f"Failed to download shard {shard_name} from any available peers.")
    
    return output_file