# client_node/auditor.py

import os
import json
import random
import time
import requests

# These imports are now relative, assuming auditor.py is in client_node
from network import peer_client
from config import Config

# --- Configuration ---
METADATA_DIR = "file_metadata"
# --- MODIFIED: Save ledger in the shared metadata directory ---
LEDGER_FILE = os.path.join(METADATA_DIR, "ledger.json")
AUDIT_INTERVAL_SECONDS = 20
REWARD_THRESHOLD = 100

config = Config()
REGISTRY_HOST = config.REGISTRY_HOST
REGISTRY_PORT = config.REGISTRY_PORT
API_KEY = config.SECRET_KEY

# --- Helper Functions ---

def load_ledger():
    """Loads the audit ledger from a JSON file, creating it if it doesn't exist."""
    if not os.path.exists(LEDGER_FILE):
        return {}
    with open(LEDGER_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_ledger(ledger):
    """Saves the audit ledger to a JSON file."""
    os.makedirs(METADATA_DIR, exist_ok=True) # Ensure directory exists
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger, f, indent=4)

# --- Reward Processing Logic ---

def process_rewards():
    """Calculates scores and issues rewards based on the ledger."""
    print("\n--- 💰 Processing Rewards ---")
    ledger = load_ledger()
    if not ledger:
        print("Ledger is empty. No rewards to process.")
        return

    for peer_id, data in ledger.items():
        data.setdefault("successful_audits", 0)
        data.setdefault("failed_audits", 0)
        data.setdefault("tokens_issued", 0)
        
        total_score = (data["successful_audits"] * 10) - (data["failed_audits"] * 25)
        
        total_tokens_eligible = 0
        if total_score > 0:
            total_tokens_eligible = total_score // REWARD_THRESHOLD
            
        newly_earned_tokens = total_tokens_eligible - data["tokens_issued"]

        if newly_earned_tokens > 0:
            print(f"🎉 CONGRATULATIONS: Peer '{peer_id}' has earned {newly_earned_tokens} new reward token(s)!")
            ledger[peer_id]["tokens_issued"] += newly_earned_tokens
            print(f"   (Total tokens issued to this peer: {ledger[peer_id]['tokens_issued']})")
        else:
            print(f"Peer '{peer_id}': No new rewards earned. (Success: {data['successful_audits']}, Failed: {data['failed_audits']}, Issued: {data['tokens_issued']})")

    save_ledger(ledger)
    print("--- Reward processing complete. ---")

# --- Main Audit Logic ---

def run_audit_cycle():
    """Performs a single, random audit of one shard on one peer."""
    print("\n---  Auditors are observing the network... ---")

    try:
        online_peers = peer_client.get_peers_from_registry(REGISTRY_HOST, REGISTRY_PORT)
        if not online_peers:
            print("AUDIT: No peers are online. Skipping audit cycle.")
            return
    except Exception as e:
        print(f"AUDIT ERROR: Could not get peer list from registry: {e}")
        return

    metadata_files = [f for f in os.listdir(METADATA_DIR) if f.endswith(".manifest.json")]
    if not metadata_files:
        print("AUDIT: No files have been uploaded yet. Skipping audit cycle.")
        return

    random_manifest_filename = random.choice(metadata_files)
    file_id = random_manifest_filename.replace(".manifest.json", "")
    
    manifest_path = os.path.join(METADATA_DIR, random_manifest_filename)
    shard_map_path = os.path.join(METADATA_DIR, f"{file_id}.shard_map.json")

    try:
        with open(manifest_path, 'r') as f: manifest = json.load(f)
        with open(shard_map_path, 'r') as f: shard_map = json.load(f)
    except Exception: return

    if not manifest['shards']: return
    random_shard_info = random.choice(manifest['shards'])
    shard_index = str(random_shard_info['index'])
    shard_name = random_shard_info['shard']
    expected_hash = random_shard_info['sha256']

    peers_with_shard = shard_map.get(shard_index, [])
    if not peers_with_shard: return
    
    target_peer_url = None
    random.shuffle(peers_with_shard)
    for peer in peers_with_shard:
        peer_address = peer.replace("http://", "")
        if peer_address in online_peers:
            target_peer_url = peer
            break
    
    if not target_peer_url: return

    print(f"AUDITING: Challenging peer '{target_peer_url}' for shard '{shard_name}'...")
    headers = {"X-API-KEY": API_KEY}
    
    try:
        response = requests.get(f"{target_peer_url}/audit-shard/{shard_name}", headers=headers, timeout=5)
        response.raise_for_status()
        
        peer_response = response.json()
        reported_hash = peer_response.get("hash")
        
        ledger = load_ledger()
        peer_id = target_peer_url
        ledger.setdefault(peer_id, {"successful_audits": 0, "failed_audits": 0, "tokens_issued": 0})

        if reported_hash == expected_hash:
            ledger[peer_id]["successful_audits"] += 1
            print(f"✅ AUDIT SUCCESS: Peer '{target_peer_url}' has the correct shard.")
        else:
            ledger[peer_id]["failed_audits"] += 1
            print(f"❌ AUDIT FAILED: Peer '{target_peer_url}' returned a mismatched hash!")
        save_ledger(ledger)
    except Exception as e:
        print(f"❌ AUDIT FAILED: Could not complete audit for peer '{target_peer_url}': {e}")

if __name__ == "__main__":
    print("---  Decentralized Storage Auditor starting up ---")
    while True:
        run_audit_cycle()
        process_rewards()
        print(f"--- Waiting for {AUDIT_INTERVAL_SECONDS} seconds until next audit cycle. ---")
        time.sleep(AUDIT_INTERVAL_SECONDS)