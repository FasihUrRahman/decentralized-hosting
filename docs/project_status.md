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
- Manifest contains:
  - Original file name
  - Shard names and indexes
  - SHA-256 hash of encrypted content for integrity check

### 4. **Shard Storage API**
- **POST** `/store-shard/` accepts file shards and stores them in a secure, encrypted format.
- **GET** `/get-shard/{index}` retrieves and decrypts specific shards.

### 5. **Shard Distribution to Peers**
- Distributes shards to peer URLs in round-robin using `distribute_shards_to_peers()`.
- Uploads shards to `/store-shard/` endpoint on peer servers.
- Saves peer-shard mapping in `shard_map.json`.

### 6. **File Reconstruction**
- `reconstruct_file_from_shards()` reads `manifest.json` and downloads shards to rebuild the original file.
- Performs integrity verification using SHA-256 before decryption.

### 7. **Basic Peer Server**
- Basic FastAPI peer server implemented to receive shard uploads and respond to retrieval requests.

---

## 🔧 Remaining Features / TODO

### ⚙️ Functional Enhancements
- [ ] **Multi-peer Redundancy**  
  Ensure each shard is stored on multiple peers (not just one).

- [ ] **Shard Retrieval Across Peers**  
  Reconstruct file by pulling shards from multiple peers using `shard_map.json`.

### 🔐 Security & Permissions
- [ ] **Authentication/Authorization**  
  Protect APIs to avoid unauthorized access.

- [ ] **Signed URLs or tokens for retrieval**

### 🔁 Peer Management
- [ ] **Dynamic Peer Discovery**  
  Discover and register peers automatically.

- [ ] **Optional: DHT or Central Registry**

### 🧠 Smart Behavior
- [ ] **Storage-aware Distribution**  
  Distribute shards based on peer storage availability.

- [ ] **Fault Tolerance**  
  Retry mechanism for failed shard uploads.  
  Health check of peer nodes.

### 🧪 Testing & Debugging
- [ ] Unit tests for:
  - Encryption/Decryption
  - Shard splitting/joining
  - Manifest integrity

- [ ] Integration tests across peers

### 🖼️ UI / Dashboard (optional)
- [ ] File upload form with progress indicator
- [ ] Peer overview and shard distribution map

---

## 📁 Directory Structure (Current)
├── README.md
├── backend/
├── frontend/
├── docs/
│ └── architecture.md
│ └── mvp_features.md
│ └── project_status.md
├── client_node/
│ └── metadata/
│ └── │ └── chunks/
│ └── │ └── │ └── a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
├── metadata/
│ └── node_state.json
├── network/
│ └── peer_client.py
│ └── peer_server.py
│ └── replicator.py
├── registry/
│ └── registry_server.py
├── shards/
│ └── manifest.json
│ └── shard_0.bin
├── storage/
│ └── disk_manager.py
├── stored_shards/
│ └── shard_1.bin
├── utils/
│ └── crypto.py
│ └── directory.py
│ └── shard_handler.py
├── cli.py
├── config.py
├── encryption.key
├── main.py
├── shard_api.py
├── test_peer_to_peer.py
├── test_sharding.py
├── test.txt
