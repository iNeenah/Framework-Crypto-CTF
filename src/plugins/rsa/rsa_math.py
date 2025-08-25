#!/usr/bin/env python3
"""
Implementación de matemáticas RSA sin dependencias externas
Alternativa a gmpy2 para producción
"""
import random
import math
from typing import Tuple, Optional

class RSAMath:
    """Implementación de operaciones matemáticas RSA sin gmpy2"""
    
    @staticmethod
    def gcd(a: int, b: int) -> int:
        """Algoritmo de Euclides para GCD"""
        while b:
            a, b = b, a % b
        return a
    
    @staticmethod
    def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        """Algoritmo de Euclides extendido"""
        if a == 0:
            return b, 0, 1
        
        gcd, x1, y1 = RSAMath.extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        
        return gcd, x, y
    
    @staticmethod
    def mod_inverse(a: int, m: int) -> Optional[int]:
        """Inverso modular usando Euclides extendido"""
        gcd, x, y = RSAMath.extended_gcd(a % m, m)
        if gcd != 1:
            return None  # No existe inverso
        return (x % m + m) % m
    
    @staticmethod
    def pow_mod(base: int, exp: int, mod: int) -> int:
        """Exponenciación modular eficiente"""
        if mod == 1:
            return 0
        
        result = 1
        base = base % mod
        
        while exp > 0:
            if exp % 2 == 1:
                result = (result * base) % mod
            exp = exp >> 1
            base = (base * base) % mod
        
        return result
    
    @staticmethod
    def is_prime_miller_rabin(n: int, k: int = 5) -> bool:
        """Test de primalidad Miller-Rabin"""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        # Escribir n-1 como d * 2^r
        r = 0
        d = n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        # Test de Miller-Rabin k veces
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = RSAMath.pow_mod(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
            
            for _ in range(r - 1):
                x = RSAMath.pow_mod(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    @staticmethod
    def pollard_rho(n: int, max_iterations: int = 100000) -> Optional[int]:
        """Algoritmo Pollard's rho para factorización"""
        if n % 2 == 0:
            return 2
        
        def f(x):
            return (x * x + 1) % n
        
        x = 2
        y = 2
        d = 1
        
        iterations = 0
        while d == 1 and iterations < max_iterations:
            x = f(x)
            y = f(f(y))
            d = RSAMath.gcd(abs(x - y), n)
            iterations += 1
        
        if d == n:
            return None
        return d if d > 1 else None
    
    @staticmethod
    def trial_division(n: int, limit: int = 10000) -> Optional[int]:
        """División de prueba hasta el límite"""
        if n % 2 == 0:
            return 2
        
        for i in range(3, min(int(n**0.5) + 1, limit), 2):
            if n % i == 0:
                return i
        
        return None
    
    @staticmethod
    def factorize(n: int) -> list:
        """Factorización usando múltiples métodos"""
        if n < 2:
            return []
        
        factors = []
        
        # Factores de 2
        while n % 2 == 0:
            factors.append(2)
            n //= 2
        
        # División de prueba para números pequeños
        factor = RSAMath.trial_division(n)
        while factor:
            factors.append(factor)
            n //= factor
            if n == 1:
                break
            factor = RSAMath.trial_division(n)
        
        # Si queda un número grande, usar Pollard's rho
        if n > 1:
            if RSAMath.is_prime_miller_rabin(n):
                factors.append(n)
            else:
                factor = RSAMath.pollard_rho(n)
                if factor:
                    factors.extend(RSAMath.factorize(factor))
                    factors.extend(RSAMath.factorize(n // factor))
                else:
                    factors.append(n)  # No se pudo factorizar
        
        return sorted(factors)
    
    @staticmethod
    def chinese_remainder_theorem(remainders: list, moduli: list) -> Optional[int]:
        """Teorema del resto chino"""
        if len(remainders) != len(moduli):
            return None
        
        total = 0
        prod = 1
        for m in moduli:
            prod *= m
        
        for r, m in zip(remainders, moduli):
            p = prod // m
            inv = RSAMath.mod_inverse(p, m)
            if inv is None:
                return None
            total += r * p * inv
        
        return total % prod
    
    @staticmethod
    def wiener_attack(n: int, e: int) -> Optional[Tuple[int, int]]:
        """Ataque de Wiener para exponentes pequeños"""
        def continued_fraction(n, d):
            """Fracción continua"""
            cf = []
            while d:
                cf.append(n // d)
                n, d = d, n % d
            return cf
        
        def convergents(cf):
            """Convergentes de fracción continua"""
            convergents = []
            h_prev, h_curr = 0, 1
            k_prev, k_curr = 1, 0
            
            for a in cf:
                h_next = a * h_curr + h_prev
                k_next = a * k_curr + k_prev
                convergents.append((h_next, k_next))
                h_prev, h_curr = h_curr, h_next
                k_prev, k_curr = k_curr, k_next
            
            return convergents
        
        # Fracción continua de e/n
        cf = continued_fraction(e, n)
        convs = convergents(cf)
        
        for k, d in convs:
            if k == 0:
                continue
            
            # Verificar si d es la clave privada
            if (e * d - 1) % k == 0:
                phi = (e * d - 1) // k
                
                # Resolver ecuación cuadrática para p y q
                s = n - phi + 1
                discriminant = s * s - 4 * n
                
                if discriminant >= 0:
                    sqrt_disc = int(discriminant ** 0.5)
                    if sqrt_disc * sqrt_disc == discriminant:
                        p = (s + sqrt_disc) // 2
                        q = (s - sqrt_disc) // 2
                        
                        if p * q == n and p > 1 and q > 1:
                            return (p, q)
        
        return None
    
    @staticmethod
    def hastad_attack(ciphertexts: list, moduli: list, e: int = 3) -> Optional[int]:
        """Ataque de Håstad para exponente pequeño"""
        if len(ciphertexts) < e or len(moduli) < e:
            return None
        
        # Usar teorema del resto chino
        result = RSAMath.chinese_remainder_theorem(ciphertexts[:e], moduli[:e])
        if result is None:
            return None
        
        # Calcular raíz e-ésima
        return RSAMath.nth_root(result, e)
    
    @staticmethod
    def nth_root(n: int, k: int) -> Optional[int]:
        """Calcular raíz k-ésima entera"""
        if n < 0:
            return None
        if n == 0:
            return 0
        if k == 1:
            return n
        
        # Búsqueda binaria
        low = 0
        high = n
        
        while low <= high:
            mid = (low + high) // 2
            mid_k = mid ** k
            
            if mid_k == n:
                return mid
            elif mid_k < n:
                low = mid + 1
            else:
                high = mid - 1
        
        return None
    
    @staticmethod
    def common_modulus_attack(c1: int, c2: int, e1: int, e2: int, n: int) -> Optional[int]:
        """Ataque de módulo común"""
        gcd, s, t = RSAMath.extended_gcd(e1, e2)
        
        if gcd != 1:
            return None
        
        if s < 0:
            c1 = RSAMath.mod_inverse(c1, n)
            s = -s
        
        if t < 0:
            c2 = RSAMath.mod_inverse(c2, n)
            t = -t
        
        if c1 is None or c2 is None:
            return None
        
        return (RSAMath.pow_mod(c1, s, n) * RSAMath.pow_mod(c2, t, n)) % n