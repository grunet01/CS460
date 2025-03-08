#!/usr/bin/env python3
"""
A5/1 cipher implementation

@authors:
@version: 2025.3
"""

from pathlib import Path


def majority(x8_bit: int, y10_bit: int, z10_bit: int) -> int:
    """Return the majority bit

    :param x8_bit: 9th bit from the X register
    :param y10_bit: 11th bit from the Y register
    :param z10_bit: 11th bit from the Z register
    :return: the value of the majority bit
    """
    return 0 if [x8_bit, y10_bit, z10_bit].count(0) >= 2 else 1


def step_x(register: list[int]) -> None:
    """Stepping register X

    :param register: X register
    """
    new_bit = register[13] ^ register[16] ^ register[17] ^ register[18]
    register.insert(0, new_bit)
    register.pop()


def step_y(register: list[int]) -> None:
    """Stepping register Y

    :param register: Y register
    """
    new_bit = register[20] ^ register[21]
    register.insert(0, new_bit)
    register.pop()


def step_z(register: list[int]) -> None:
    """Stepping register Z

    :param register: Z register
    """
    new_bit = register[7] ^ register[20] ^ register[21] ^ register[22]
    register.insert(0, new_bit)
    register.pop()


def generate_bit(x: list[int], y: list[int], z: list[int]) -> int:
    """Generate a keystream bit

    :param x: X register
    :param y: Y register
    :param z: Z register
    :return: a single keystream bit
    """
    return x[18] ^ y[21] ^ z[22]


def generate_keystream(plaintext_chars: int, x: list[int], y: list[int], z: list[int]) -> list[int]:
    """Generate stream of bits to match length of plaintext

    :param plaintext: plaintext to be encrypted
    :param x: X register
    :param y: Y register
    :param z: Z register
    :return: keystream of the same length as the plaintext
    """
    keystream = []
    for _ in range(0, plaintext_chars * 8):
        maj = majority(x[8], y[10], z[10])

        if x[8] == maj: step_x(x)
        if y[10] == maj: step_y(y)
        if z[10] == maj: step_z(z)

        keystream.append(generate_bit(x, y, z))

    return keystream



def populate_registers(init_keyword: str) -> tuple[list[int], list[int], list[int]]:
    """Populate registers

    Important: if the keyword is shorted than 8 characters (64 bits),
    pad the resulting short bit string with zeros (0) up to the required 64 bits

    :param init_keyword: initial secret word that will be used to populate registers X, Y, and Z
    :return: registers X, Y, Z
    """

    binary_list = []
     
    for char in init_keyword:
        byte = bin(ord(char))[2:].zfill(8)
        bit_list = []
        for bit in byte:
            bit_list.append(int(bit))

        binary_list.extend(bit_list)

    if len(binary_list) < 64:
        binary_list.extend([0] * (64 - len(binary_list)))
         
    x_register = binary_list[:19]
    y_register = binary_list[19:41]
    z_register = binary_list[41:]
    
    return tuple([x_register, y_register, z_register])


def xor_with_keystream(bits: str, keystream: list[int]) -> str:
    return ''.join(str(int(bit) ^ k) for bit, k in zip(bits, keystream))

def encrypt(plaintext: str, keystream: list[int]) -> bytes:
    """Encrypt plaintext using A5/1

    :param plaintext: plaintext to be encrypted
    :param keystream: keystream
    :return: ciphertext
    """
    plaintext_bits = ''.join(format(ord(char), '08b') for char in plaintext)
    cipher_bits = xor_with_keystream(plaintext_bits, keystream)
    ciphertext = bytes(int(cipher_bits[i:i+8], 2) for i in range(0, len(cipher_bits), 8))
    return ciphertext


def decrypt(ciphertext: bytes, keystream: list[int]) -> str:
    """Decrypt ciphertext using A5/1

    :param ciphertext: ciphertext to be decrypted
    :param keystream: keystream
    :return: plaintext
    """
    cipher_bits = ''.join(format(byte, '08b') for byte in ciphertext)
    plaintext_bits = xor_with_keystream(cipher_bits, keystream)
    plaintext = ''.join(chr(int(plaintext_bits[i:i+8], 2)) for i in range(0, len(plaintext_bits), 8))
    return plaintext


def encrypt_file(source: Path, secret: str, destination: Path | None = None) -> None:
    """Encrypt a file

    :param source: file to be encrypted
    :param secret: secret to initialize registers
    :param destination: encrypted file (if None, will use source with .secret suffix)
    """
    plaintext = source.read_text(encoding="utf-8")
    x, y, z = populate_registers(secret)
    keystream = generate_keystream(len(plaintext), x, y, z)
    ciphertext = encrypt(plaintext, keystream)
    
    if destination is None:
        destination = source.with_suffix(".secret")
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    destination.write_bytes(ciphertext)


def decrypt_file(source: Path, secret: str, destination: Path | None = None) -> None:
    """Decrypt a file

    :param source: file to be decrypted
    :param secret: secret to initialize registers
    :param destination: decrypted file (optional)
    """
    ciphertext = source.read_bytes()
    x, y, z = populate_registers(secret)
    keystream = generate_keystream(len(ciphertext), x, y, z)
    plaintext = decrypt(ciphertext, keystream)

    if destination is None:
        destination = source.with_suffix(".txt")

    destination.parent.mkdir(parents=True, exist_ok=True)

    destination.write_text(plaintext, encoding="utf-8", newline="\n")


def main():
    """Main function"""
    #PROJECT_DIR = Path("data/projects/a51/")
    #encrypt_file(DIR / "hello.txt", "123456789012", DIR / "hello.secret")
    #decrypt_file(DIR / "hello.secret", "123456789012", DIR / "hello.txt")

    print("The 10 secret files are the first 10 ammendments to the constitution: the Bill of Rights.")


if __name__ == "__main__":
    main()
