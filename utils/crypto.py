import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def text_to_binary(text: str) -> str:
    binary = ''.join(format(ord(char), '08b') for char in text)
    return binary

def binary_to_text(binary: str) -> str:
    if len(binary) % 8 != 0:
        padding = 8 - (len(binary) % 8)
        binary += '0' * padding
        
    bytes_data = bytearray()
    for i in range(0, len(binary), 8):
        byte = int(binary[i:i+8], 2)
        bytes_data.append(byte)
    
    return bytes_data

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt(message: str, password: str) -> str:
    salt = os.urandom(16)  
    key = generate_key_from_password(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return base64.urlsafe_b64encode(salt + encrypted).decode()

def decrypt(encrypted_message: str, password: str) -> str:
    try:
        data = base64.urlsafe_b64decode(encrypted_message)
        salt = data[:16]
        encrypted = data[16:]
        key = generate_key_from_password(password, salt)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        return f"Decryption failed: {str(e)}"

# def encrypt(message: str, password: str) -> str:
#     key = hashlib.sha256(password.encode()).digest()
#     message_bytes = message.encode() if isinstance(message, str) else message
#     encrypted = bytearray(len(message_bytes))
#     for i in range(len(message_bytes)):
#         encrypted[i] = message_bytes[i] ^ key[i % len(key)]
#     return base64.b64encode(encrypted).decode()

# def decrypt(encrypted_message: str, password: str) -> str:
#     try:
#         encrypted_bytes = base64.b64decode(encrypted_message)
#         key = hashlib.sha256(password.encode()).digest()
#         decrypted = bytearray(len(encrypted_bytes))
#         for i in range(len(encrypted_bytes)):
#             decrypted[i] = encrypted_bytes[i] ^ key[i % len(key)]
        
#         return decrypted.decode('utf-8', errors='replace')
#     except Exception as e:
#         return str(decrypted)