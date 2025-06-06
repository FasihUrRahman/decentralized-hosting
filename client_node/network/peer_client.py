# client_node/network/peer_client.py
import socket
import base64
import time # <-- NEW IMPORT

def send_store_request(host, port, chunk_data: bytes):
    msg = "STORE " + base64.b64encode(chunk_data).decode()
    return _send(host, port, msg)

def send_fetch_request(host, port, chunk_id: str):
    msg = "FETCH " + chunk_id
    return _send(host, port, msg)

def _send(host, port, message: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, int(port)))
        s.sendall(message.encode())
        response = s.recv(4096).decode()
        return response

def get_peers_from_registry(host, port):
    """Connects to the registry and gets a list of active peers, with retries."""
    # --- NEW: Retry Logic ---
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(b"GET PEERS")
                data = s.recv(4096).decode()
                peers = [line.strip() for line in data.strip().split("\n") if line.strip()]
                return peers
        except ConnectionRefusedError:
            print(f"Registry connection refused. Retrying in 2 seconds... ({attempt + 1}/{max_retries})")
            time.sleep(2)
    # If all retries fail, raise an exception
    raise ConnectionError("Could not connect to the registry after several attempts.")
    # --- End of NEW ---