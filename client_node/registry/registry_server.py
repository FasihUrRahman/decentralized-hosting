# client_node/registry/registry_server.py

import socket
import threading
import time

class RegistryServer:
    def __init__(self, host="0.0.0.0", port=6000):
        self.host = host
        self.port = port
        self.peers = []
        self.lock = threading.Lock()
        self.health_check_interval = 20  # Check every 20 seconds

    def start(self):
        print(f"🌐 Registry Server listening on {self.host}:{self.port}")
        
        health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        health_thread.start()
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(4096).decode().strip()

            if data.startswith("REGISTER"):
                parts = data.split()
                if len(parts) == 2 and ":" in parts[1]:
                    peer_host, peer_port = parts[1].split(":")
                    with self.lock:
                        peer = (peer_host, int(peer_port))
                        if peer not in self.peers:
                            self.peers.append(peer)
                            print(f"✅ Registered peer: {peer_host}:{peer_port}")
                    conn.sendall(b"REGISTERED")
                else:
                    conn.sendall(b"ERROR Invalid registration format")

            elif data == "GET PEERS":
                with self.lock:
                    peer_list = "\n".join([f"{host}:{port}" for host, port in self.peers])
                conn.sendall(peer_list.encode())

            else:
                conn.sendall(b"INVALID COMMAND")

        except Exception as e:
            print(f"❌ Registry error with {addr}: {e}")
        finally:
            conn.close()

    def health_check_loop(self):
        """Periodically checks if registered peers are still online."""
        while True:
            time.sleep(self.health_check_interval)
            
            with self.lock:
                peers_to_check = self.peers[:]
            
            if not peers_to_check:
                continue

            print(f"\n🩺 Running health checks on {len(peers_to_check)} peer(s)...")

            for peer_host, peer_port in peers_to_check:
                try:
                    with socket.create_connection((peer_host, peer_port), timeout=3):
                        pass
                    print(f"👍 Peer {peer_host}:{peer_port} is healthy.")
                except (socket.timeout, ConnectionRefusedError):
                    print(f"👎 Peer {peer_host}:{peer_port} is offline. Removing.")
                    with self.lock:
                        if (peer_host, peer_port) in self.peers:
                            self.peers.remove((peer_host, peer_port))

# This block is what starts the server.
# It was likely missing from your file.
if __name__ == "__main__":
    server = RegistryServer()
    server.start()