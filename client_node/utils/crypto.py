# utils/crypto.py
import os
import binascii
from cryptography.fernet import Fernet, InvalidToken
import base64

KEY_FILE = "encryption.key"

def generate_key():
    """Generate and save a new Fernet key"""
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"🔑 Generated new encryption key")
    return key

def load_key():
    """Load the encryption key, generate if doesn't exist"""
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

def get_cipher_suite():
    """Return a Fernet instance with the loaded key"""
    key = load_key()
    return Fernet(key)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data with validation"""
    if not isinstance(data, bytes):
        raise TypeError(f"Expected bytes, got {type(data)}")
    
    try:
        cipher = get_cipher_suite()
        encrypted = cipher.encrypt(data)
        print(f"🔒 Encrypted {len(data)} bytes")
        return encrypted
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}") from e

def decrypt_data(encrypted_data: bytes) -> bytes:
    """Decrypt data with comprehensive error handling"""
    if not isinstance(encrypted_data, bytes):
        try:
            encrypted_data = encrypted_data.encode()
        except AttributeError:
            raise TypeError("Expected bytes or string")
    
    try:
        # Verify minimum length (Fernet token is always > 60 bytes)
        if len(encrypted_data) < 60:
            raise ValueError("Data too short to be Fernet token")
            
        # Handle potential padding issues
        try:
            cipher = get_cipher_suite()
            return cipher.decrypt(encrypted_data)
        except InvalidToken:
            # Try with padding correction
            missing_padding = len(encrypted_data) % 4
            if missing_padding:
                encrypted_data += b'=' * (4 - missing_padding)
                return cipher.decrypt(encrypted_data)
            raise
    except Exception as e:
        print(f"❌ Decryption failed. Possible causes:")
        print(f"- Key changed since encryption (current key: {load_key()[:10]}...)")
        print(f"- Data corrupted (length: {len(encrypted_data)} bytes)")
        print(f"- First bytes: {encrypted_data[:32]}...")
        raise ValueError(f"Decryption failed: {str(e)}") from e