# client_node/auditor.py

import os
import json
import random
import time
import requests

from network import peer_client
from config import Config

# --- Configuration ---
METADATA_DIR = "file_metadata"
LEDGER_FILE = "ledger.json"
AUDIT_INTERVAL_SECONDS = 20 # Shortened for easier testing
REWARD_THRESHOLD = 100 # Lowered for easier testing (10 successful audits)

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
            return {} # Return empty dict if file is empty or corrupt

def save_ledger(ledger):
    """Saves the audit ledger to a JSON file."""
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger, f, indent=4)

# --- NEW: Reward Processing Logic ---

def process_rewards():
    """Calculates scores and issues rewards based on the ledger."""
    print("\n--- 💰 Processing Rewards ---")
    ledger = load_ledger()
    if not ledger:
        print("Ledger is empty. No rewards to process.")
        return

    for peer_id, data in ledger.items():
        score = (data.get("successful_audits", 0) * 10) - (data.get("failed_audits", 0) * 25)
        
        print(f"Peer '{peer_id}': Score is {score}. Successful={data['successful_audits']}, Failed={data['failed_audits']}")

        if score >= REWARD_THRESHOLD:
            rewards_earned = score // REWARD_THRESHOLD
            points_spent = rewards_earned * REWARD_THRESHOLD
            
            # Simulate issuing a reward
            print(f"🎉 CONGRATULATIONS: Peer '{peer_id}' has earned {rewards_earned} reward token(s)!")
            
            # "Spend" the points by reducing the success count accordingly
            # This is a simple way to reset their score for the next reward
            audits_to_clear = points_spent // 10
            ledger[peer_id]["successful_audits"] -= audits_to_clear
    
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
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        with open(shard_map_path, 'r') as f:
            shard_map = json.load(f)
    except Exception:
        return # Skip if metadata is incomplete

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
        if peer_id not in ledger:
            ledger[peer_id] = {"successful_audits": 0, "failed_audits": 0}

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
        process_rewards() # <-- NEW: Process rewards after each audit
        print(f"--- Waiting for {AUDIT_INTERVAL_SECONDS} seconds until next audit cycle. ---")
        time.sleep(AUDIT_INTERVAL_SECONDS)