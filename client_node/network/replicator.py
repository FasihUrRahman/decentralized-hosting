import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from network.peer_client import send_store_request

class Replicator:
    def __init__(self, redundancy_factor=3):
        self.redundancy_factor = redundancy_factor
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)  # Add basic logging

    def replicate_chunk(self, chunk_data: bytes, peers: list) -> list:
        """Enhanced replication with detailed logging"""
        stored_peers = []
        
        def _store_task(peer):
            host, port = peer
            try:
                response = send_store_request(host, port, chunk_data)
                if response.startswith("STORED"):
                    self.logger.info(f"Stored on {host}:{port}")
                    return peer
                else:
                    self.logger.warning(f"Unexpected response from {host}:{port}: {response}")
            except Exception as e:
                self.logger.error(f"Failed to store on {host}:{port}: {str(e)}")
            return None

        # Try storing on all peers in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_store_task, peer) for peer in peers]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    stored_peers.append(result)
                    if len(stored_peers) >= self.redundancy_factor:
                        break

        return stored_peers

# Singleton instance
replicator = Replicator()