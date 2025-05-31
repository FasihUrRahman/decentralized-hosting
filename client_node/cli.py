# cli.py
from network.peer_client import send_store_request, send_fetch_request
import base64

def main():
    print("📁 Decentralized Storage CLI")
    print("1. Store File")
    print("2. Fetch Chunk")
    choice = input("Choose an option: ")

    if choice == "1":
        filename = input("Enter filename: ")
        with open(filename, "rb") as f:
            data = f.read()
        response = send_store_request("localhost", 5001, data)
        print("📤 STORE Response:", response)
    elif choice == "2":
        chunk_id = input("Enter chunk ID: ")
        response = send_fetch_request("localhost", 5001, chunk_id)
        if response.startswith("DATA "):
            b64_data = response.split(" ", 1)[1]
            decoded = base64.b64decode(b64_data)
            with open("output_file", "wb") as f:
                f.write(decoded)
            print("✅ Saved to output_file")
        else:
            print("❌ Fetch failed.")

if __name__ == "__main__":
    main()
