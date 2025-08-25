# SekaiCTF 2023 - diffecientwo_solution
# Fuente: https://github.com/project-sekai-ctf/sekaictf-2023/tree/main/crypto
# Descargado: 2025-08-25 00:37:29
# Desafío: diffecientwo_solution
# Año: 2023

---

import pwn

proc = pwn.remote("chals.sekai.team", 3000)

with open("found_keys.txt", "rb") as f:
    hashes = f.read().strip().split()

for h in hashes:
    proc.sendline(b'2')
    proc.sendline(h)

proc.sendline(b'3')
proc.interactive()
