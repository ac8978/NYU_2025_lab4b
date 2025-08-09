import sqlite3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

# Set environment variable
os.environ['AES_KEY'] = '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1234'

def encrypt_password(password):
    key = bytearray.fromhex(os.getenv('AES_KEY'))
    nonce = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return nonce + tag + ciphertext

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
# Create or update users table
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, password BLOB, act_token TEXT)''')
# Encrypt a test password (e.g., "test123")
encrypted = encrypt_password("test123")
# Insert or update user (adjust token as needed)
cursor.execute("INSERT OR REPLACE INTO users (user_id, password, act_token) VALUES (?, ?, ?)", (1, encrypted, "!Q#E%T&U8i6y4r2w"))
conn.commit()
conn.close()
