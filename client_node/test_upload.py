# client_node/test_upload.py

import requests
import os

# The URL of our new main API server
UPLOAD_URL = "http://localhost:8080/upload/"

# The file we want to upload
TEST_FILE_NAME = "my_document_to_upload.txt"

def run_upload_test():
    print(f"--- Starting upload test for {TEST_FILE_NAME} ---")
    
    # 1. Create a dummy file to upload
    with open(TEST_FILE_NAME, "w") as f:
        f.write("This is a test document for the decentralized hosting platform.\n")
        f.write("It contains multiple lines of text.\n" * 50)
        f.write("End of document.\n")
    
    # 2. Prepare the file for the POST request
    with open(TEST_FILE_NAME, "rb") as f:
        files = {"file": (TEST_FILE_NAME, f, "text/plain")}
        
        # 3. Send the request to the upload endpoint
        print(f"📤 Uploading {TEST_FILE_NAME} to {UPLOAD_URL}...")
        try:
            response = requests.post(UPLOAD_URL, files=files, timeout=30) # Increased timeout for processing
            response.raise_for_status() # Raise an exception for bad status codes
            
            # 4. Print the result
            print("✅ Success! Server responded with:")
            print(response.json())
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error during upload: {e}")
            
    # 5. Clean up the dummy file
    os.remove(TEST_FILE_NAME)
    print("\n--- Test complete ---")

if __name__ == "__main__":
    run_upload_test()