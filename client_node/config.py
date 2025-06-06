import os

class Config:
    def __init__(self):
        self.port = int(os.getenv("NODE_PORT", 5001))
        self.max_storage_mb = int(os.getenv("MAX_STORAGE_MB", 500))  # 500MB default

