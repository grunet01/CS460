import sqlite3
import bcrypt
import hashlib
import math

# For AES encryption/decryption
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

DATABASE = 'passman.db'
APP_SECRET = '7nrAygsU5eFDXR5u1LRvXYK1uc5Zj4cM'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the account table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            key TEXT NOT NULL
        )
    ''')

    # Create the profile table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user INTEGER NOT NULL,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            expires TEXT,
            FOREIGN KEY (user) REFERENCES account (id)
        )
    ''')

    conn.commit()
    conn.close()

def calculate_entropy(password):

    charset_size = 0
    if any(c.islower() for c in password):
        charset_size += 26
    if any(c.isupper() for c in password):
        charset_size += 26
    if any(c.isdigit() for c in password):
        charset_size += 10

    special_chars = set("!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~")
    if any(c in special_chars for c in password):
        charset_size += 32
    if charset_size == 0:
        return 0
    return len(password) * math.log2(charset_size)

def classify_entropy(entropy_bits):

    if entropy_bits < 50:
        return "Weak"
    elif entropy_bits < 80:
        return "Acceptable"
    else:
        return "Strong"

def encrypt_AES(plaintext, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return iv.hex() + ciphertext.hex()

def decrypt_AES(encrypted_hex, key):
    iv = bytes.fromhex(encrypted_hex[:32])
    ciphertext = bytes.fromhex(encrypted_hex[32:])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode('utf-8')

def create_account(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM account WHERE username=?", (username,))
    row = cursor.fetchone()
    if row is not None:
        conn.close()
        return False, None, None  
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    key_bytes = hashlib.scrypt(
        password.encode('utf-8'),
        salt=APP_SECRET.encode('utf-8'),
        n=16384,
        r=8,
        p=1,
        dklen=32
    )
    key_hex = key_bytes.hex()
    cursor.execute("""
        INSERT INTO account (username, password, key)
        VALUES (?, ?, ?)
    """, (username, hashed_password.decode('utf-8'), key_hex))
    conn.commit()
    account_id = cursor.lastrowid
    conn.close()
    return True, account_id, key_hex

def verify_account(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, key FROM account WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False, None, None
    stored_password = row["password"]
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        return True, row["id"], row["key"]
    else:
        return False, None, None

def add_profile(user_id, name, username, password, expires, account_key_hex):
    conn = get_db_connection()
    cursor = conn.cursor()
    key = bytes.fromhex(account_key_hex)
    encrypted_username = encrypt_AES(username, key)
    encrypted_password = encrypt_AES(password, key)
    cursor.execute("""
        INSERT INTO profile (user, name, username, password, expires)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, encrypted_username, encrypted_password, expires))
    conn.commit()
    conn.close()

def get_profiles_by_user(user_id, account_key_hex):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE user=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    key = bytes.fromhex(account_key_hex)
    profiles = []
    for row in rows:
        profile = dict(row)
        profile['username'] = decrypt_AES(profile['username'], key)
        profile['password'] = decrypt_AES(profile['password'], key)
        entropy = calculate_entropy(profile['password'])
        strength = classify_entropy(entropy)
        profile['strength'] = strength
        profiles.append(profile)
    return profiles


def get_profile_by_id(profile_id, user_id, account_key_hex):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE id=? AND user=?", (profile_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    key = bytes.fromhex(account_key_hex)
    profile = dict(row)
    profile['username'] = decrypt_AES(profile['username'], key)
    profile['password'] = decrypt_AES(profile['password'], key)
    return profile

def update_profile(profile_id, user_id, name, username, password, expires, account_key_hex):
    conn = get_db_connection()
    cursor = conn.cursor()
    key = bytes.fromhex(account_key_hex)
    encrypted_username = encrypt_AES(username, key)
    encrypted_password = encrypt_AES(password, key)
    cursor.execute("""
        UPDATE profile
        SET name = ?, username = ?, password = ?, expires = ?
        WHERE id = ? AND user = ?
    """, (name, encrypted_username, encrypted_password, expires, profile_id, user_id))
    conn.commit()
    conn.close()

def delete_profile(profile_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profile WHERE id=? AND user=?", (profile_id, user_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized")
