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
            if hashlib.sha256(encrypted).hexdigest() != shard_info['sha256']:
                raise ValueError(f"Hash mismatch for {shard_info['shard']}")
            decrypted = decrypt_data(encrypted)
            out.write(decrypted)
    print(f"✅ File reconstructed successfully at: {output_file}")

def distribute_shards_to_peers(manifest_path: str, shard_dir: str, peer_urls: list[str], api_key: str, replicas: int = 2, shard_map_path="shard_map.json"):
    """
    Distributes shards to peers with fault tolerance. If an upload fails,
    it tries another available peer.
    """
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    headers = {"X-API-KEY": api_key}
    shard_map = {}

    for shard_info in manifest['shards']:
        index = shard_info['index']
        shard_map[index] = []
        
        # --- NEW Fault-Tolerant Logic ---
        
        # Shuffle the list of peers to try them in a random order
        available_peers = random.sample(peer_urls, len(peer_urls))
        peers_tried = set()
        
        while len(shard_map[index]) < replicas:
            if not available_peers:
                print(f"⚠️ Warning: Ran out of peers for shard {index}. Stored {len(shard_map[index])}/{replicas} replicas.")
                break

            peer = available_peers.pop(0)
            
            shard_file_path = os.path.join(shard_dir, shard_info['shard'])
            try:
                with open(shard_file_path, 'rb') as f_shard:
                    files = {"shard": (shard_info['shard'], f_shard, "application/octet-stream")}
                    data = {"index": index}
                    
                    print(f"📤 Attempting to send shard {index} to {peer}...")
                    r = requests.post(f"{peer}/store-shard/", files=files, data=data, headers=headers, timeout=5)
                    r.raise_for_status()
                    
                    print(f"✅ Shard {index} successfully sent to {peer}")
                    shard_map[index].append(peer)

            except requests.RequestException as e:
                print(f"❌ Failed to send shard {index} to {peer}: {e}. Trying next peer.")
        # --- End of NEW Logic ---

    with open(shard_map_path, "w") as f:
        json.dump(shard_map, f, indent=2)
    print(f"✅ Shard map saved to {shard_map_path}")
    return shard_map_path

def reconstruct_from_peers(manifest_path: str, shard_map_path: str, output_file: str, api_key: str):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    with open(shard_map_path, 'r') as f:
        shard_map = json.load(f)

    headers = {"X-API-KEY": api_key}
    temp_shard_dir = "downloaded_shards"
    if os.path.exists(temp_shard_dir):
        shutil.rmtree(temp_shard_dir)
    os.makedirs(temp_shard_dir)

    print(f"🚀 Starting reconstruction of '{manifest['original_file']}'...")
    for shard_info in manifest['shards']:
        index_str = str(shard_info['index'])
        if index_str not in shard_map or not shard_map[index_str]:
            raise RuntimeError(f"No peers found for shard {index_str}")
        
        peer_urls = shard_map[index_str]
        downloaded = False
        for peer_url in peer_urls:
            try:
                print(f"📥 Attempting to download shard {index_str} from {peer_url}...")
                response = requests.get(f"{peer_url}/get-shard/{index_str}", headers=headers, timeout=10)
                response.raise_for_status()
                
                shard_path = os.path.join(temp_shard_dir, shard_info['shard'])
                with open(shard_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Successfully downloaded shard {index_str}.")
                downloaded = True
                break
            except requests.RequestException as e:
                print(f"⚠️ Could not fetch shard {index_str} from {peer_url}: {e}")
        
        if not downloaded:
            shutil.rmtree(temp_shard_dir)
            raise ConnectionError(f"Failed to download shard {index_str}")
    try:
        reconstruct_file_from_shards(manifest_path, temp_shard_dir, output_file)
    finally:
        shutil.rmtree(temp_shard_dir)