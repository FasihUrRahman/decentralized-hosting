import os
import hashlib
from utils.crypto import encrypt_data, decrypt_data

STORAGE_DIR = "client_node/metadata/chunks"

class DiskManager:
    def __init__(self, max_storage_mb):
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def _chunk_path(self, chunk_id):
        return os.path.join(STORAGE_DIR, chunk_id)

    def save_chunk(self, chunk_data: bytes) -> str:
        """Store chunk as-is without re-encrypting"""
        chunk_id = hashlib.sha256(chunk_data).hexdigest()
        path = self._chunk_path(chunk_id)

        if not os.path.exists(path):
            if self.get_used_space() + len(chunk_data) > self.max_storage_bytes:
                raise Exception("Storage limit reached!")
            with open(path, "wb") as f:
                f.write(chunk_data)

        return chunk_id

    def load_chunk(self, chunk_id: str) -> bytes:
        """Return raw chunk data without decryption"""
        path = self._chunk_path(chunk_id)
        if not os.path.exists(path):
            raise FileNotFoundError("Chunk not found.")
        with open(path, "rb") as f:
            return f.read()

    def get_used_space(self):
        total = 0
        for filename in os.listdir(STORAGE_DIR):
            path = os.path.join(STORAGE_DIR, filename)
            if os.path.isfile(path):
                total += os.path.getsize(path)
        return total
