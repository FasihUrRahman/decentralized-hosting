import socket
from network.peer_server import PeerServer
from storage.disk_manager import DiskManager
import base64

def main():
    print("🔌 Starting Decentralized Host Node...")
    disk = DiskManager(500)
    port = 5002
    print(f"📦 Max Storage Allowed: {disk.max_storage_bytes // (1024 * 1024)} MB")
    print(f"🌐 Listening on port {port}")
    print(f"💽 Used disk: {disk.get_used_space() / 1024:.2f} KB")

    server = PeerServer(port)
    server.start()

    chunk_id = "afa27b44d43b02a9fea41d13cedc2e4016cfcf87c5dbf990e593669aa8ce286d"

    try:
        chunk_data = disk.load_chunk(chunk_id)
        print(f"✅ Already had chunk: {chunk_data}")
    except FileNotFoundError:
        print("⚠️ Chunk not found locally, trying to fetch from peers...")
        peers = server.get_peers_from_registry()
        found = False

        for host, port in peers:
            if f"{host}:{port}" == "127.0.0.1:5002":
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((host, int(port)))
                    s.sendall(f"FETCH {chunk_id}".encode())
                    response = s.recv(65536).decode()
                    if response.startswith("DATA "):
                        base64_data = response[5:]
                        chunk_data = base64.b64decode(base64_data)
                        disk.save_chunk(chunk_data)
                        print(f"✅ Successfully fetched and saved chunk from peer: {chunk_data}")
                        found = True
                        break
            except Exception as e:
                print(f"❌ Could not fetch from peer {host}:{port} — {e}")
        
        if not found:
            print("🚫 Chunk not found in any peer.")

if __name__ == "__main__":
    main()
