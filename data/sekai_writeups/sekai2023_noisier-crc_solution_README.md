# SekaiCTF 2023 - noisier-crc_solution
# Fuente: https://github.com/project-sekai-ctf/sekaictf-2023/tree/main/crypto
# Descargado: 2025-08-25 00:37:32
# Desafío: noisier-crc_solution
# Año: 2023

---

## Solution

In the writeup of the previous challenge, we claim that the secret has the form

$$\sum_{i} c_{i, j_i}A_i$$

If we use the same idea, all $A_i$ has degree $16n$, and we have $13n$ basis. Give that $n \le 133$ we won't be able to recover the 512-bit secret. The trick is to modify the equation to

$$\text{secret} + \sum_{i} c_{i, 0}A_i = \sum_{i} (c_{i, j_i} - c_{i, 0})A_i$$

Now the left hand side is spanned by $12n$ basis instead of $13n$, and we can recover unique secret up to $4 \times 133 = 532$ bits.
