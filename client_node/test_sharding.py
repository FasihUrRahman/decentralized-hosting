from utils.shard_handler import process_file_to_shards, reconstruct_file_from_shards, distribute_shards_to_peers

input_file = "test.txt"
shard_folder = "shards"
output_file = "restored_example.txt"

manifest = process_file_to_shards(input_file, shard_folder)

# List of peer URLs (make sure at least one client_node server is running)
peers = [
    "http://localhost:8000"  # You can spin up multiple FastAPI apps on diff ports
]

# Send shards to peers
distribute_shards_to_peers(manifest, shard_folder, peers)

# Optional: reconstruct from local shards for testing
# reconstruct_file_from_shards(manifest, shard_folder, output_file)
