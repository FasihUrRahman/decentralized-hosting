# registry/registry_server.py

import socket
import threading

class RegistryServer:
    def __init__(self, host="0.0.0.0", port=6000):
        self.host = host
        self.port = port
        self.peers = []
        self.lock = threading.Lock()

    def start(self):
        print(f"🌐 Registry Server listening on {self.host}:{self.port}")
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
                if len(parts) == 2:
                    ip_port = parts[1]
                    if ":" in ip_port:
                        peer_host, peer_port = ip_port.split(":")
                        with self.lock:
                            peer = (peer_host, peer_port)
                            if peer not in self.peers:
                                self.peers.append(peer)
                                print(f"✅ Registered peer: {peer_host}:{peer_port}")
                        conn.sendall(b"REGISTERED")
                    else:
                        conn.sendall(b"ERROR Invalid IP:Port format")
                else:
                    conn.sendall(b"ERROR Invalid registration format")

            elif data == "GET PEERS":
                with self.lock:
                    peer_list = "\n".join([f"{host}:{port}" for host, port in self.peers])
                conn.sendall(peer_list.encode())

            else:
                conn.sendall(b"INVALID COMMAND")

        except Exception as e:
            print(f"❌ Registry error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    server = RegistryServer()
    server.start()
