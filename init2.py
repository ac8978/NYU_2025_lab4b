import sqlite3
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Set environment variable
os.environ['AES_KEY'] = '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1234'

def encrypt_password(password):
    key = bytearray.fromhex(os.getenv('AES_KEY'))
    if len(key) != 32:
        raise ValueError("AES_KEY must be 32 bytes")
    nonce = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return (nonce + tag + ciphertext).hex()

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row  # Enable dictionary-like row access
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, password TEXT, act_token TEXT)''')
# User 1
encrypted1 = encrypt_password("test123")
cursor.execute("INSERT OR REPLACE INTO users (user_id, password, act_token) VALUES (?, ?, ?)", 
              (1, encrypted1, "!Q#E%T&U8i6y4r2w"))
# User 2
encrypted2 = encrypt_password("test123")
cursor.execute("INSERT OR REPLACE INTO users (user_id, password, act_token) VALUES (?, ?, ?)", 
              (2, encrypted2, "AnotherToken12345"))
conn.commit()
# Query and print encrypted passwords
cursor.execute("SELECT user_id, password, length(password) FROM users")
for row in cursor.fetchall():
    print(f"User {row['user_id']}: password hex = {row['password']}, length = {row['length(password)']}")
conn.close()
print("Database initialized with two users, password 'test123'")


