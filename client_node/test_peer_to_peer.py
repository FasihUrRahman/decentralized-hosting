from network.peer_client import send_store_request, send_fetch_request

# Store a chunk
response = send_store_request("localhost", 5001, b"this-is-a-remote-test")
print("📤 STORE Response:", response)

# Extract chunk_id
if response.startswith("STORED "):
    chunk_id = response.split(" ")[1]
    
    # Fetch the chunk back
    response = send_fetch_request("localhost", 5001, chunk_id)
    print("📥 FETCH Response:", response[:60] + "...")
else:
    print("❌ Store failed.")
