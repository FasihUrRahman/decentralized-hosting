# network/replicator.py
from network.peer_client import send_store_request

def replicate_chunk(chunk_data, peers, copies=2):
    stored = []
    for host_port in peers:
        if len(stored) >= copies:
            break
        host, port = host_port.split(":")
        response = send_store_request(host, int(port), chunk_data)
        if response.startswith("STORED"):
            stored.append((host, port))
    return stored

