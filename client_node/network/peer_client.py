import socket
import base64

def send_store_request(host, port, chunk_data: bytes):
    msg = "STORE " + base64.b64encode(chunk_data).decode()
    return _send(host, port, msg)

def send_fetch_request(host, port, chunk_id: str):
    msg = "FETCH " + chunk_id
    return _send(host, port, msg)

def _send(host, port, message: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(message.encode())
        response = s.recv(4096).decode()
        return response

