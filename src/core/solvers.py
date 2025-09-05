# src/core/solvers.py

from pwn import remote, process
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import re

# --- Solver Implementations ---

def _symmetric_decrypt_aes_cbc(key: bytes, ciphertext: bytes) -> bytes:
    """Helper function for AES CBC decryption, adapted from the original script."""
    ct, iv = ciphertext[:-16], ciphertext[-16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt

# NEW, REFACTORED SOLVER
def solve_sekai_graph_aes(conn: remote):
    """
    Solver for the SekaiCTF 2023 'cryptography-1' challenge.
    Assumes the connection is already established.
    """
    try:
        print("[+] Solver taking control of connection.")
        # The agent should have already received the initial text.
        # The solver's job starts from the first unique prompt of the challenge logic.
        conn.recvuntil(b'[*] Key: ')
        key = bytes.fromhex(conn.recvline().strip().decode())
        print("[+] Solver received AES key.")

        for i in range(50):
            print(f"[*] Solver: Round {i+1}/50")
            conn.recvuntil(b'50: ')
            u, v = map(int, conn.recvline().strip().decode().split())
            
            conn.recvuntil(b'[*] Response: ')
            resp = bytes.fromhex(conn.recvline().strip().decode())
            
            key_ske = key[:16]
            path_parts = []
            for j in range(0, len(resp), 32):
                ct = resp[j:j+32]
                path_parts.append(_symmetric_decrypt_aes_cbc(key_ske, ct).decode())
            
            ans_nodes = [u]
            for p in path_parts:
                ans_nodes.append(int(p.split(',')[0]))
            
            ans = " ".join(map(str, ans_nodes))
            conn.sendlineafter(b'query: ', ans.encode())

        print("[+] Solver completed 50 rounds.")
        # The solver's job is done. It returns True for success.
        # The main agent will be responsible for reading the flag.
        return True

    except Exception as e:
        print(f"\n[ERROR] An error occurred within the solver: {e}")
        return False

# --- Solver Registry ---

# This dictionary maps a crypto identifier (from our classifier) to a solver function.
SOLVER_REGISTRY = {
    'Crypto.Cipher.AES': solve_sekai_graph_aes,
    'Crypto.Util.Padding.unpad': solve_sekai_graph_aes, # Also maps the padding function
    # In the future, we would add more entries here, e.g.:
    # 'Crypto.Hash.SHA256': solve_some_sha256_problem,
    # 'Crypto.PublicKey.RSA': solve_rsa_challenge,
}

def get_solver(labels: list):
    """
    Finds a suitable solver from the registry based on predicted labels.
    Returns the first matching solver found.
    """
    for label in labels:
        if label in SOLVER_REGISTRY:
            print(f"[i] Match found: Label '{label}' corresponds to solver '{SOLVER_REGISTRY[label].__name__}'.")
            return SOLVER_REGISTRY[label]
    print("[w] No suitable solver found in registry for the given labels.")
    return None