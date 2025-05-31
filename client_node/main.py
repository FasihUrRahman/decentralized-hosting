import socket
from config import Config
from network.peer_server import PeerServer
from storage.disk_manager import DiskManager
import base64

def main():
    config = Config()
    print("🔌 Starting Decentralized Host Node...")
    disk = DiskManager(config.max_storage_mb)
    port = config.port
    print(f"📦 Max Storage Allowed: {disk.max_storage_bytes // (1024 * 1024)} MB")
    print(f"🌐 Listening on port {port}")
    print(f"💽 Used disk: {disk.get_used_space() / 1024:.2f} KB")

    server = PeerServer(port)
    server.start()

    # chunk_id = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"

    # try:
    #     chunk_data = disk.load_chunk(chunk_id)
    #     print(f"✅ Already had chunk: {chunk_data}")
    # except FileNotFoundError:
    #     print("⚠️ Chunk not found locally, trying to fetch from peers...")
    #     peers = server.get_peers_from_registry()
    #     found = False

    #     for host, port in peers:
    #         if f"{host}:{port}" == "127.0.0.1:5002":
    #             continue
    #         try:
    #             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #                 s.connect((host, int(port)))
    #                 s.sendall(f"FETCH {chunk_id}".encode())
    #                 response = s.recv(65536).decode()
    #                 if response.startswith("DATA "):
    #                     base64_data = response[5:]
    #                     chunk_data = base64.b64decode(base64_data)
    #                     disk.save_chunk(chunk_data)
    #                     print(f"✅ Successfully fetched and saved chunk from peer: {chunk_data}")
    #                     found = True
    #                     break
    #         except Exception as e:
    #             print(f"❌ Could not fetch from peer {host}:{port} — {e}")
        
    #     if not found:
    #         print("🚫 Chunk not found in any peer.")

if __name__ == "__main__":
    main()
