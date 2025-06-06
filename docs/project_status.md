# 📦 Project: Decentralized Hosting
_A decentralized file hosting system using FastAPI and peer-to-peer architecture_

---

## ✅ Features Completed

### 1. **File Splitting & Sharding**
- Implemented `split_file()` to divide large files into 1MB shards.
- Each shard is indexed for easy retrieval and reconstruction.

### 2. **Encryption**
- Used `Fernet` encryption from the `cryptography` library.
- Each shard is encrypted individually before being stored or distributed.

### 3. **Manifest File**
- A `manifest.json` is generated when files are sharded.
- Manifest contains the original file name, shard details, and SHA-256 hashes for integrity checks.

### 4. **Secure Shard Storage API**
- **POST** `/store-shard/` accepts file shards and stores them.
- **GET** `/get-shard/{index}` retrieves specific shards.
- All API endpoints are now protected with API Key authentication to prevent unauthorized access.

### 5. **Redundant & Fault-Tolerant Shard Distribution**
- Each shard is distributed to multiple peers to ensure redundancy.
- The upload process is fault-tolerant; if an upload to one peer fails, the system automatically tries another available peer.

### 6. **Fault-Tolerant File Reconstruction**
- `reconstruct_from_peers()` reconstructs a file by pulling its shards from multiple peers across the network.
- If a peer is offline during a download, the system automatically fetches the required shard from another peer that holds a replica.
- Performs integrity verification using SHA-256 hashes from the manifest before decryption.

### 7. **Dynamic Peer Management**
- A central `RegistryServer` is used for peer registration and discovery.
- The registry actively monitors peer health and automatically removes offline nodes from the available peer list.

---

## 🔧 Remaining Features / TODO

### 🏆 Core Goal
- [ ] **Reward System**
  - Design and implement a system to track storage contributions from peers.
  - Integrate a crypto/token system to reward peers for their participation.

### 🧠 Smart Behavior
- [ ] **Storage-aware Distribution**
  - Distribute shards based on peer storage availability and latency.

### 🔐 Advanced Security
- [ ] **Signed URLs or tokens for retrieval**
  - Implement a more granular permission model for file access.

### 🧪 Testing & Debugging
- [ ] **Formalize Testing Suite**
  - Convert existing test scripts (`test_full_cycle.py`, etc.) into a formal testing suite using a framework like `pytest`.
  - Add comprehensive unit tests for individual functions.

### 🖼️ UI / Dashboard
- [ ] **User Frontend**
  - A dashboard for users to upload, download, and manage their files.
- [ ] **Peer/Node Dashboard**
  - A dashboard for node operators to view their storage usage, uptime, and rewards.