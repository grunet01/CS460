#!/usr/bin/python3
"""
Merkle-Hellman Knapsack cipher implementation

@authors:
@version: 2025.3
"""

LARGE_N = 100


def generate_sik(size: int) -> tuple[int, ...]:
    """
    Generate a superincreasing knapsack of the specified size
    Assuming 1-based indexing, i-th item in this knapsack is chosen uniformly from the following range:
    [pow(2, i-1) * pow(2, LARGE_N) + 1, pow(2, i-1)*pow(2, LARGE_N)]

    :param size: size (in bits) of the knapsack
    :return: a superincreasing knapsack as a tuple
    """
    sik = []
    total = 0
    
    for _ in range(size):
        next_value = total * 2 + 1 if total > 0 else 1
        sik.append(next_value)
        total += next_value

    return tuple(sik)



def calculate_n(sik: tuple) -> int:
    """
    Calculate N value

    N is the smallest number greater than the sum of values in the knapsack

    :param sik: a superincreasing knapsack
    :return: n
    """
    return sum(sik) + 1

def calculate_m(n: int) -> int:
    """
    Calculate M value

    M is the largest number in the range [1, N) that is co-prime of N
    :param n: N value
    """
    def gcd(a, b):
        # euclidean algorithm for coprime
        while b > 0:
            a, b = b, a % b
        return a

    for k in range(n - 1, 0, -1):
        if gcd(n, k) == 1:
            return k
        
    return None


def calculate_inverse(sik: tuple[int, ...], n: int = 0, m: int = 0) -> int:
    """
    Calculate inverse modulo

    :param sik: a superincreasing knapsack
    :param n: N value
    :param m: M value
    :return: inverse modulo i so that m*i = 1 mod n
    """
    
    def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
        if b == 0:
            return a, 1, 0
        else:
            gcd, x1, y1 = extended_gcd(b, a % b)
            x = y1
            y = x1 - (a // b) * y1
            return gcd, x, y
    
    if n == 0:
        n = calculate_n(sik)
    if m == 0:
        m = calculate_m(n)

    gcd, inverse, _ = extended_gcd(m, n)

    if gcd != 1:
        raise ValueError(f"{m} has no modular inverses mod {n}")
    
    return inverse % n


def generate_gk(sik: tuple[int, ...], n: int = 0, m: int = 0) -> tuple[int, ...]:
    """
    Generate a general knapsack from the provided superincreasing knapsack

    :param sik: a superincreasing knapsack
    :param n: N value
    :param m: M value
    :return: the general knapsack
    """
    if n == 0:
        n = calculate_n(sik)
    if m == 0:
        m = calculate_m(n)

    general_knapsack = []
    for value in sik:
        general_value = (value * m) % n
        general_knapsack.append(general_value)

    return tuple(general_knapsack)


def encrypt(plaintext: str, gk: tuple[int, ...]) -> int:
    """
    Encrypt a message

    :param plaintext: text to encrypt
    :param gk: general knapsack
    :return: encrypted text
    :raise: ValueError if the message is longer than the knapsack
    """
    knapsack_length = len(gk)
    binary_string = ''.join(format(ord(char), '08b') for char in plaintext)

    if len(binary_string) > knapsack_length:
        raise ValueError("Message is too long for the given knapsack.")

    binary_string = binary_string.zfill(knapsack_length)
    ciphertext = sum(int(bit) * weight for bit, weight in zip(binary_string, gk))
    
    return ciphertext
    


def decrypt(ciphertext: int, sik: tuple[int, ...], n: int = 0, m: int = 0) -> str:
    """
    Decrypt a single block.

    :param ciphertext: text to decrypt
    :param sik: superincreasing knapsack
    :param n: N value
    :param m: M value
    :return: decrypted string
    """
    m_inverse = calculate_inverse(sik, n, m)
    k = (ciphertext * m_inverse) % n

    plaintext_bits = []
    for weight in reversed(sik):
        if k >= weight:
            k -= weight
            plaintext_bits.insert(0, "1")
        else:
            plaintext_bits.insert(0, "0")

    bit_string = ''.join(plaintext_bits)
    bit_string = bit_string.lstrip("0")

    if len(bit_string) % 8 != 0:
        bit_string = bit_string.zfill((len(bit_string) + 7) // 8 * 8)

    chars = [chr(int(bit_string[i:i+8], 2)) for i in range(0, len(bit_string), 8)]

    return ''.join(chars)

    

def main():
    """
    Main function
    Use your own values to check that functions work as expected
    """


if __name__ == "__main__":
    main()
