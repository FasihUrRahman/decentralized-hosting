# client_node/test_inter_peer_communication.py
from network.peer_client import send_store_request, send_fetch_request
import time

PEER_1_HOST = "localhost"
PEER_1_PORT = 5001

PEER_2_HOST = "localhost"
PEER_2_PORT = 5002

print("--- Testing Inter-Peer Communication ---")

# 1. Store data on Peer 1
data_to_store = b"This is a test of peer-to-peer fetching."
print(f"\nSTEP 1: Storing data on Peer 1 ({PEER_1_HOST}:{PEER_1_PORT})...")
store_response = send_store_request(PEER_1_HOST, PEER_1_PORT, data_to_store)
print(f"-> Store Response from Peer 1: {store_response}")

if not store_response.startswith("STORED "):
    print("\n--- TEST FAILED: Could not store data on Peer 1. ---")
    exit()

chunk_id = store_response.split(" ")[1]
print(f"-> Data stored successfully with chunk_id: {chunk_id}")

# Give peers a moment to register and be discoverable
print("\nWaiting 2 seconds for peer discovery...")
time.sleep(2)

# 2. Fetch the same data from Peer 2
# Peer 2 should not have this data locally. It will have to ask the registry
# for other peers (i.e., Peer 1) and fetch it from them. This is the key test.
print(f"\nSTEP 2: Attempting to fetch chunk '{chunk_id}' from Peer 2 ({PEER_2_HOST}:{PEER_2_PORT})...")
print("(Peer 2 should fetch this from Peer 1 automatically)")
fetch_response = send_fetch_request(PEER_2_HOST, PEER_2_PORT, chunk_id)

if fetch_response.startswith("DATA "):
    print("-> Fetch Response from Peer 2 received.")
    print("\n--- ✅ SUCCESS: Peer 2 successfully retrieved the data from Peer 1! ---")
else:
    print(f"-> Fetch Response from Peer 2: {fetch_response}")
    print("\n--- ❌ FAILURE: Peer 2 could not retrieve the data. ---")