import socket
import threading
import base64
import time
from storage.disk_manager import DiskManager

class PeerServer:
    def __init__(self, port):
        self.port = port
        self.running = True
        self.disk = DiskManager(500)

    def register_with_registry(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", 6000))  # Registry is running locally on port 6000
                address = f"127.0.0.1:{self.port}"
                s.sendall(f"REGISTER {address}".encode())
                response = s.recv(1024).decode()
                print(f"📝 Registry response: {response}")
        except Exception as e:
            print(f"❌ Could not register with registry: {e}")

    def handle_client(self, conn, addr):
        print(f"🔗 Incoming connection from {addr}")
        try:
            data = conn.recv(4096).decode()
            print(f"📨 Received: {data[:50]}...")

            if data.startswith("STORE "):
                base64_data = data[6:].strip()
                chunk_data = base64.b64decode(base64_data)

                # Encryption handled inside DiskManager
                chunk_id = self.disk.save_chunk(chunk_data)
                conn.sendall(f"STORED {chunk_id}".encode())

            elif data.startswith("FETCH "):
                chunk_id = data[6:].strip()
                try:
                    # Decryption handled inside DiskManager
                    chunk_data = self.disk.load_chunk(chunk_id)
                    base64_chunk = base64.b64encode(chunk_data).decode()
                    conn.sendall(f"DATA {base64_chunk}".encode())

                except FileNotFoundError:
                    # Try fetching from other peers
                    found = False
                    for host, port in self.get_peers_from_registry():
                        if f"{host}:{port}" == f"127.0.0.1:{self.port}":
                            continue  # Skip self

                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
                                peer_socket.connect((host, int(port)))
                                peer_socket.sendall(f"FETCH {chunk_id}".encode())
                                response = peer_socket.recv(65536).decode()

                                if response.startswith("DATA "):
                                    base64_data = response[5:]
                                    chunk_data = base64.b64decode(base64_data)

                                    # Store the data locally (encryption handled in DiskManager)
                                    self.disk.save_chunk(chunk_data)

                                    conn.sendall(response.encode())
                                    found = True
                                    break
                        except Exception:
                            continue

                    if not found:
                        conn.sendall(b"ERROR Not Found")
            else:
                conn.sendall(b"ERROR Invalid Command")
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.sendall(f"ERROR {str(e)}".encode())
        finally:
            conn.close()

    def get_peers_from_registry(self):
        peers = []
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("localhost", 6000))
                s.sendall(b"GET PEERS")
                data = s.recv(4096).decode()
                for line in data.strip().split("\n"):
                    if line:
                        host, port = line.strip().split(":")
                        peers.append((host, port))
        except Exception as e:
            print(f"⚠️ Could not fetch peers: {e}")
        return peers

    def start(self):
        self.register_with_registry()
        thread = threading.Thread(target=self.run_server)
        thread.start()

    def run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", self.port))
            s.listen()
            print(f"✅ Peer node is listening on port {self.port}...")

            while self.running:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
