# tests/test_api.py

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import io
import hashlib

# We need to test both the peer API and the main orchestrator API
from client_node.shard_api import app as shard_api_app
from client_node.main_api import app as main_api_app
from client_node.config import Config

# --- Fixtures to create test clients for our two main APIs ---

@pytest_asyncio.fixture
async def peer_client():
    """ A test client for the peer node API (shard_api.py) """
    async with AsyncClient(transport=ASGITransport(app=shard_api_app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def main_client():
    """ A test client for the main user-facing API (main_api.py) """
    async with AsyncClient(transport=ASGITransport(app=main_api_app), base_url="http://test") as client:
        yield client

# --- Test Cases ---

@pytest.mark.asyncio
async def test_health_check(peer_client: AsyncClient):
    """ Tests if the /health endpoint on the peer node is working correctly. """
    print("\nTesting /health endpoint...")
    response = await peer_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ /health endpoint is working!")


@pytest.mark.asyncio
async def test_peer_shard_handling(peer_client: AsyncClient):
    """
    Tests a peer's ability to store, delete, and verify deletion of a shard.
    This is a unit/integration test for the shard_api itself.
    """
    print("\n--- Testing Peer Shard Handling ---")
    config = Config()
    headers = {"X-API-KEY": config.SECRET_KEY}

    # 1. STORE SHARD
    print("Step 1: Storing a shard directly on a peer...")
    shard_content = b"This is the content of a single test shard."
    shard_hash = hashlib.sha256(shard_content).hexdigest()
    shard_filename = f"{shard_hash}.bin"
    
    files_to_upload = {"shard": (shard_filename, io.BytesIO(shard_content), "application/octet-stream")}

    store_response = await peer_client.post("/store-shard/", files=files_to_upload, headers=headers)
    assert store_response.status_code == 200
    print(f"✅ Shard '{shard_filename}' stored successfully.")

    # 2. DELETE SHARD
    print(f"\nStep 2: Deleting shard '{shard_filename}'...")
    delete_response = await peer_client.delete(f"/delete-shard/{shard_filename}", headers=headers)
    assert delete_response.status_code == 200
    print("✅ Deletion request successful.")

    # 3. VERIFY DELETION
    print(f"\nStep 3: Verifying shard deletion...")
    verify_response = await peer_client.get(f"/get-shard/{shard_filename}", headers=headers)
    assert verify_response.status_code == 404 # Expect "Not Found"
    print("✅ Verification successful. Shard is no longer available.")
    print("\n--- Peer Shard Handling Test Passed! ---")


@pytest.mark.asyncio
async def test_full_file_lifecycle(main_client: AsyncClient):
    """
    Tests the entire file lifecycle via the main_api.
    """
    print("\n--- Testing Full File Lifecycle ---")
    
    # 1. UPLOAD
    print("Step 1: Uploading file via main_api...")
    file_content = b"This is the content of our test file for the full lifecycle test."
    file_to_upload = {"file": ("test_lifecycle.txt", io.BytesIO(file_content), "text/plain")}
    
    upload_response = await main_client.post("/upload/", files=file_to_upload)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    print(f"✅ Upload successful. File ID: {file_id}")

    # 2. DOWNLOAD
    print(f"\nStep 2: Downloading file with ID {file_id}...")
    download_response = await main_client.get(f"/download/{file_id}")
    assert download_response.status_code == 200
    assert download_response.content == file_content
    print("✅ Download successful. Content matches original.")

    # 3. DELETE
    print(f"\nStep 3: Deleting file with ID {file_id}...")
    delete_response = await main_client.delete(f"/delete/{file_id}")
    assert delete_response.status_code == 200
    print("✅ Deletion request successful.")

    # 4. VERIFY DELETION
    print(f"\nStep 4: Verifying deletion by attempting to download again...")
    verify_response = await main_client.get(f"/download/{file_id}")
    assert verify_response.status_code == 404
    print("✅ Verification successful. File is no longer available.")
    print("\n--- Full Lifecycle Test Passed! ---")