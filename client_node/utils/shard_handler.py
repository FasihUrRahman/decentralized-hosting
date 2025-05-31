# utils/shard_handler.py

import os
import json
import hashlib
import requests
from utils.crypto import encrypt_data, decrypt_data

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
        for shard in sorted(manifest['shards'], key=lambda x: x['index']):
            shard_file = os.path.join(shard_dir, shard['shard'])

            with open(shard_file, 'rb') as f:
                encrypted = f.read()

            # Integrity check
            if hashlib.sha256(encrypted).hexdigest() != shard['sha256']:
                raise ValueError(f"Hash mismatch for {shard['shard']}")

            decrypted = decrypt_data(encrypted)
            out.write(decrypted)

    print(f"✅ File reconstructed at: {output_file}")

def distribute_shards_to_peers(manifest_path: str, shard_dir: str, peer_urls: list[str], shard_map_path="shard_map.json"):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    shard_map = {}

    for i, shard in enumerate(manifest['shards']):
        peer = peer_urls[i % len(peer_urls)]  # round robin
        shard_file = os.path.join(shard_dir, shard['shard'])

        with open(shard_file, 'rb') as f:
            files = {
                "shard": (shard['shard'], f, "application/octet-stream")
            }
            data = {
                "index": shard['index']
            }
            try:
                r = requests.post(f"{peer}/store-shard/", files=files, data=data)
                if r.status_code == 200:
                    print(f"📤 Shard {shard['index']} sent to {peer}")
                    shard_map[shard['index']] = peer
                else:
                    print(f"❌ Failed to send shard {shard['index']} to {peer}: {r.text}")
            except Exception as e:
                print(f"❌ Error sending to {peer}: {str(e)}")

    with open(shard_map_path, "w") as f:
        json.dump(shard_map, f, indent=2)
    
    print(f"✅ Shard map saved to {shard_map_path}")