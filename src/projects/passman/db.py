import sqlite3
import bcrypt
import hashlib

# For AES encryption/decryption
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

DATABASE = 'passman.db'

def get_db_connection():
    """Establish a connection to the SQLite3 database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they do not exist."""
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
            username TEXT NOT NULL,  -- Encrypted using AES
            password TEXT NOT NULL,  -- Encrypted using AES
            expires TEXT,
            FOREIGN KEY (user) REFERENCES account (id)
        )
    ''')

    conn.commit()
    conn.close()

def encrypt_AES(plaintext, key):
    """
    Encrypt the plaintext using AES (CBC mode) with the provided key.
    Returns a hex string that concatenates the IV and the ciphertext.
    """
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    # Return IV and ciphertext as hex strings concatenated together.
    return iv.hex() + ciphertext.hex()

def decrypt_AES(encrypted_hex, key):
    """
    Decrypt a hex-encoded string (IV + ciphertext) using AES (CBC mode)
    and the provided key.
    """
    iv = bytes.fromhex(encrypted_hex[:32])  # first 16 bytes (32 hex chars)
    ciphertext = bytes.fromhex(encrypted_hex[32:])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode('utf-8')

def create_or_verify_account(username, password):
    """
    If the account does not exist, create it by hashing the password with bcrypt
    and deriving a 256-bit key using scrypt.
    If the account exists, verify the given password against the stored hash.
    
    Returns a tuple: (success: bool, account_id: int or None, account_key: str or None)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, key FROM account WHERE username=?", (username,))
    row = cursor.fetchone()

    if row is None:
        # Account does not exist: create a new account.
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Derive a 256-bit key using scrypt (using the username as salt for demonstration)
        key_bytes = hashlib.scrypt(
            password.encode('utf-8'),
            salt=username.encode('utf-8'),
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
    else:
        # Account exists: verify the password.
        stored_password = row["password"]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            conn.close()
            return True, row["id"], row["key"]
        else:
            conn.close()
            return False, None, None

def add_profile(user_id, name, username, password, expires, account_key_hex):
    """
    Encrypt the profile's username and password using AES and insert
    a new record into the profile table.
    """
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
    """
    Retrieve all profiles for a given user and decrypt the username and password.
    """
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
        profiles.append(profile)
    return profiles

def update_profile(profile_id, user_id, name, username, password, expires, account_key_hex):
    """
    Update a profile record with new values. The username and password are
    encrypted using AES.
    """
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
    """
    Delete a profile record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profile WHERE id=? AND user=?", (profile_id, user_id))
    conn.commit()
    conn.close()

def get_profile_by_id(profile_id, user_id, account_key_hex):
    """
    Retrieve and decrypt a single profile for a given user.
    Returns a dictionary with profile details or None if not found.
    """
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


if __name__ == '__main__':
    init_db()
    print("Database initialized and tables created (if they did not already exist).")
