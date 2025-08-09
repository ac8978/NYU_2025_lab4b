from flask import render_template, Flask, request, redirect
import os
import infinc
import SampleNetworkClient
import sqlite3
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import socket

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to encrypt the password using AES encryption
def encrypt_password(password):
    # Load key from environment variable
    key_str = os.getenv('AES_KEY')
    if not key_str:
        raise ValueError("AES_KEY environment variable not set")
    key = bytearray.fromhex(key_str)  # Expect 32-byte key in hex (64 chars)
    if len(key) != 32:
        raise ValueError("AES_KEY must be 32 bytes (64 hex characters)")
    
    # Generate random nonce for each encryption
    nonce = get_random_bytes(16)  # 16-byte nonce for AES-EAX
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return nonce + tag + ciphertext

# Verify password
def verify_password(conn, user_password):
    db_query = "SELECT * FROM users"
    db_result = conn.execute(db_query).fetchone()
    db_password = db_result['password']  # Assumes column name 'password'
    # Extract nonce (16 bytes), tag (16 bytes), and ciphertext (remaining)
    nonce = db_password[:16]
    tag = db_password[16:32]
    ciphertext = db_password[32:]
    
    # Load key from environment variable
    key_str = os.getenv('AES_KEY')
    if not key_str:
        raise ValueError("AES_KEY environment variable not set")
    key = bytearray.fromhex(key_str)
    if len(key) != 32:
        raise ValueError("AES_KEY must be 32 bytes (64 hex characters)")
    
    # Decrypt and verify
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    try:
        decrypted_password = cipher.decrypt_and_verify(ciphertext, tag)
        if decrypted_password.decode() == user_password:
            act_token = db_result['act_token']  # Assumes column name 'token'
            return True, act_token
    except ValueError:
        pass  # Decryption or verification failed
    return False, ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        conn = get_db_connection()
        password = request.form.get('authToken')
        try:
            is_password, act_token = verify_password(conn, password)
            if is_password:
                snc = SampleNetworkClient.SimpleNetworkClient(23456, 23457)
                is_auth = snc.authenticate(23456, bytes(act_token, 'utf-8'))
                return render_template('authenticate.html', Temp="0.00", Token=is_auth.decode('utf-8'))
            else:
                db_message = ''
                db_query = "SELECT * FROM users WHERE password = ?"  # Secure against SQL injection
                db_password = conn.execute(db_query, (password,)).fetchone()
                if db_password:
                    for x in db_password:
                        db_message = db_message + ":" + str(x)
                    return render_template('login.html', Err=str(db_message))
                return render_template('login.html', Err="Wrong password")
        except Exception as ex:
            return render_template('login.html', Err=str(ex))
        finally:
            conn.close()

@app.route('/get_temp', methods=['POST'])
def start_infinc():
    auth_token = request.form.get('authToken')
    snc = SampleNetworkClient.SimpleNetworkClient(23456, 23457)
    try:
        temp = snc.getTemperatureFromPort(23456, auth_token)
    except Exception:
        temp = "Bad Token"
    return render_template('authenticate.html', Token=auth_token, Temp=temp)

@app.route('/set_temp_c', methods=['POST'])
def set_temp_c():
    auth_token = request.form.get('authToken')
    snc = SampleNetworkClient.SimpleNetworkClient(23456, 23457)
    try:
        temp_change = snc.setTemperatureC(23456, auth_token)
        temp = snc.getTemperatureFromPort(23456, auth_token)
    except Exception as ex:
        temp = "Bad Token"
    return render_template('authenticate.html', Token=auth_token, Temp=temp)

@app.route('/set_temp_f', methods=['POST'])
def set_temp_f():
    auth_token = request.form.get('authToken')
    snc = SampleNetworkClient.SimpleNetworkClient(23456, 23457)
    try:
        temp_change = snc.setTemperatureF(23456, auth_token)
        temp = snc.getTemperatureFromPort(23456, auth_token)
    except Exception as ex:
        temp = "Bad Token"
    return render_template('authenticate.html', Token=auth_token, Temp=temp)

@app.route('/set_temp_k', methods=['POST'])
def set_temp_k():
    auth_token = request.form.get('authToken')
    snc = SampleNetworkClient.SimpleNetworkClient(23456, 23457)
    try:
        temp_change = snc.setTemperatureK(23456, auth_token)
        temp = snc.getTemperatureFromPort(23456, auth_token)
    except Exception as ex:
        temp = "Bad Token"
    return render_template('authenticate.html', Token=auth_token, Temp=temp)
