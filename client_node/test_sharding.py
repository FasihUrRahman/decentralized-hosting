import os
from utils.shard_handler import (
    process_file_to_shards,
    distribute_shards_to_peers
)

# Test configuration
input_file = "test.txt"
shard_folder = "shards"
peers = ["localhost:5001", "localhost:5002", "localhost:5003"]

def run_test():
    # 1. Process file into shards
    manifest_path = process_file_to_shards(input_file, shard_folder)
    
    # 2. Distribute to peers
    try:
        distribute_shards_to_peers(manifest_path, shard_folder, peers)
        print("✅ Test completed successfully")
    except Exception as e:
        print(f"❌ Distribution failed: {str(e)}")
        # Print peer status
        for peer in peers:
            host, port = peer.split(":")
            try:
                response = send_fetch_request(host, int(port), "status")
                print(f"{peer}: {response}")
            except Exception as e:
                print(f"{peer}: ❌ {str(e)}")

if __name__ == "__main__":
    # Verify test file exists
    if not os.path.exists(input_file):
        with open(input_file, 'w') as f:
            f.write("This is a test file for decentralized hosting.")
    
    run_test()