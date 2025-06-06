# client_node/config.py
import os

class Config:
    def __init__(self):
        self.port = int(os.getenv("NODE_PORT", 5001))
        self.max_storage_mb = int(os.getenv("MAX_STORAGE_MB", 500))  # 500MB default
        
        # --- NEW ---
        # This is the secret key that all peers in your private network must share.
        # For real-world use, this should be loaded securely (e.g., from an environment variable).
        self.SECRET_KEY = "N6LF6W7lSu-NkROGZ3YBJr6CE79i5PZ2bbiVcEqx9ao="
        self.REGISTRY_HOST = os.getenv("REGISTRY_HOST", "localhost")
        self.REGISTRY_PORT = int(os.getenv("REGISTRY_PORT", 6000))