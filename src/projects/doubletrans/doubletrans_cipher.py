#!/usr/bin/env python3
"""
Double transposition cipher implementation

@authors: Ethan Grunewald
@version: 2025.2
"""

import string
from pathlib import Path
import itertools

def load_word_list() -> set[str]:
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]
    word_file = project_root / "data" / "projects" / "doubletrans" / "words"
    return {line.strip().lower() for line in word_file.read_text(encoding="utf-8").splitlines() if line.strip()}

ENGLISH_WORDS = load_word_list()
PUNCTUATION_TABLE = str.maketrans('', '', string.punctuation)

def encrypt(plaintext: str, key: tuple[tuple[int, ...], tuple[int, ...]]) -> str:
    """Encrypt plaintext using double transposition cipher with direct string manipulation

    :param plaintext: plaintext
    :param key: (row_permutation, column_permutation) as tuples of ints
    :return: ciphertext
    """
    row_transposition, col_transposition = key
    rows, cols = len(row_transposition), len(col_transposition)

    padding = (rows * cols) - len(plaintext)
    padded = plaintext.upper() + ("*" * padding)

    ciphertext_chars = []
    for i in range(rows):
        for j in range(cols):
            src_index = row_transposition[i] * cols + col_transposition[j]
            ciphertext_chars.append(padded[src_index])
    return ''.join(ciphertext_chars)



def decrypt(ciphertext: str, key: tuple[tuple[int, ...], tuple[int, ...]]) -> str:
    """Decrypt ciphertext using double transposition cipher

    :param ciphertext: ciphertext
    :param key: rows and columns permutations
    :return: plaintext
    """

    def invert_indices(key: tuple[int, ...]) -> tuple[int, ...]:
        inverse = [0] * len(key)
        for i, k in enumerate(key):
            inverse[k] = i
        return tuple(inverse)

    inverse_key = (invert_indices(key[0]), invert_indices(key[1]))
    decrypted_text = encrypt(ciphertext, inverse_key)
    plaintext = decrypted_text.replace("*", '').lower()

    return plaintext


def analyze(ciphertext: str) -> set[str]:
    """Analyze ciphertext generated using double transposition cipher

    :param ciphertext: encrypted text to analyze
    :return: set of plaintext candidate(s)
    """
    def permutations(elements):
        if len(elements) <= 1:
            yield elements
            return
        for perm in permutations(elements[1:]):
            for i in range(len(elements)):
                yield perm[:i] + elements[0:1] + perm[i:]

    def factor_pairs(n):
        i = 2
        while i * i <= n:
            if n % i == 0:
                yield (i, n // i)
                if i != n // i:
                    yield (n // i, i)
            i += 1

    def is_candidate(decrypted: str):
        star_index = decrypted.find('*')
        if star_index != -1:
            if any(ch != '*' for ch in decrypted[star_index:]):
                return False
            decrypted = decrypted[:star_index]

        if '  ' in decrypted:
            return False
        
        decrypted_words = decrypted.translate(PUNCTUATION_TABLE).split()
        if not decrypted_words:
            return False
        return all(word.lower() in ENGLISH_WORDS for word in decrypted_words)
    

    def try_all_permutations(text, dimensions):
        rows_list = list(range(dimensions[0]))
        cols_list = list(range(dimensions[1]))

        candidate_list = []

        for row_permutation in itertools.permutations(rows_list):
            for col_permutation in itertools.permutations(cols_list):
                decrypted = decrypt(text, (row_permutation, col_permutation))
                if is_candidate(decrypted):
                    candidate_list.append(decrypted)

        return set(candidate_list)


    gen_matrix_dimensions = factor_pairs(len(ciphertext))
    for dimensions in gen_matrix_dimensions:

        permutation_result = try_all_permutations(ciphertext,dimensions)
        
        if len(permutation_result) > 0:
            return permutation_result
    
    return []
        


def main():
    """Main function"""
    print("Phrases to decrypt:")
    phrases = [
        #' AEWHVA EU NHSOT,OR*E OLBMP', 
        'MISENHTOWEGIDKC HW IA STCSYO*EM ',
        'TTYME ESR.OY RTDNGI EOSHF EPT OR HPREROSE A   IOMNFT',
        "TRRONE FOMS.Y UR,OORFF N IT M'NOI , EWRDITJU YS DSFE TIFASE,RTNGRMLI YEAA , RCZY"
        ]

    for phrase in phrases:
        print(phrase)
        print('Candidates:')
        print("    " + str(analyze(phrase)))
    


if __name__ == "__main__":
    main()
