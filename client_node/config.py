import os

class Config:
    def __init__(self):
        self.port = int(os.getenv("NODE_PORT", 5002))
        self.max_storage_mb = int(os.getenv("MAX_STORAGE_MB", 500))
        self.SECRET_KEY = "N6LF6W7lSu-NkROGZ3YBJr6CE79i5PZ2bbiVcEqx9ao="
        self.REGISTRY_HOST = os.getenv("REGISTRY_HOST", "localhost")
        self.REGISTRY_PORT = int(os.getenv("REGISTRY_PORT", 6000))
        self.PEER_HOSTNAME = os.getenv("PEER_HOSTNAME", "127.0.0.1")