import sqlite3
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import unittest
from app import encrypt_password, verify_password, get_db_connection

class TestEncryption(unittest.TestCase):
    def setUp(self):
        # Set environment variable
        os.environ['AES_KEY'] = '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1234'
        # Initialize test database
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE users (user_id INTEGER PRIMARY KEY, password BLOB, act_token TEXT)''')
        # Encrypt and store a test password
        password = "test123"
        encrypted = encrypt_password(password)
        self.cursor.execute("INSERT INTO users (user_id, password, act_token) VALUES (?, ?, ?)", 
                          (1, encrypted, "!Q#E%T&U8i6y4r2w"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_key_from_env(self):
        # Test that encryption fails without AES_KEY
        del os.environ['AES_KEY']
        with self.assertRaises(ValueError) as cm:
            encrypt_password("test123")
        self.assertEqual(str(cm.exception), "AES_KEY environment variable not set")
        # Restore key for other tests
        os.environ['AES_KEY'] = '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1234'

    def test_random_nonce(self):
        # Test that encrypting the same password twice produces different outputs
        password = "test123"
        encrypted1 = encrypt_password(password)
        encrypted2 = encrypt_password(password)
        self.assertNotEqual(encrypted1, encrypted2, "Nonces should ensure different ciphertexts")
        # Check nonce difference (first 16 bytes)
        self.assertNotEqual(encrypted1[:16], encrypted2[:16], "Nonces should be different")

    def test_verify_correct_password(self):
        # Test successful login
        is_valid, act_token = verify_password(self.conn, "test123")
        self.assertTrue(is_valid, "Correct password should validate")
        self.assertEqual(act_token, "!Q#E%T&U8i6y4r2w", "Token should match stored value")

    def test_verify_incorrect_password(self):
        # Test failed login
        is_valid, act_token = verify_password(self.conn, "wrongpass")
        self.assertFalse(is_valid, "Incorrect password should fail")
        self.assertEqual(act_token, "", "No token should be returned for incorrect password")

if __name__ == '__main__':
    unittest.main()
