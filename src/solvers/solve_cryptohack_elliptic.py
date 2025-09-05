#!/usr/bin/env python3
"""
Solucionador para Desafío de Curvas Elípticas - CryptoHack
=========================================================
Implementa el algoritmo Double and Add para multiplicación escalar
"""

class EllipticCurve:
    def __init__(self, a, b, p):
        """
        Curva elíptica: y² = x³ + ax + b mod p
        """
        self.a = a
        self.b = b
        self.p = p
        
    def is_on_curve(self, point):
        """Verifica si un punto está en la curva"""
        if point is None:  # Punto en el infinito
            return True
        
        x, y = point
        return (y * y) % self.p == (x * x * x + self.a * x + self.b) % self.p
    
    def point_double(self, point):
        """Duplica un punto en la curva elíptica"""
        if point is None:  # Punto en el infinito
            return None
        
        x, y = point
        
        # Calcular la pendiente: λ = (3x² + a) / (2y) mod p
        numerator = (3 * x * x + self.a) % self.p
        denominator = (2 * y) % self.p
        
        # Calcular el inverso modular
        lambda_val = (numerator * self.mod_inverse(denominator, self.p)) % self.p
        
        # Calcular el nuevo punto
        x_new = (lambda_val * lambda_val - 2 * x) % self.p
        y_new = (lambda_val * (x - x_new) - y) % self.p
        
        return (x_new, y_new)
    
    def point_add(self, p1, p2):
        """Suma dos puntos en la curva elíptica"""
        # Punto en el infinito
        if p1 is None:
            return p2
        if p2 is None:
            return p1
        
        x1, y1 = p1
        x2, y2 = p2
        
        # Si son el mismo punto, usar point_double
        if x1 == x2 and y1 == y2:
            return self.point_double(p1)
        
        # Si tienen la misma x pero diferente y, el resultado es infinito
        if x1 == x2:
            return None
        
        # Calcular la pendiente: λ = (y2 - y1) / (x2 - x1) mod p
        numerator = (y2 - y1) % self.p
        denominator = (x2 - x1) % self.p
        
        lambda_val = (numerator * self.mod_inverse(denominator, self.p)) % self.p
        
        # Calcular el nuevo punto
        x_new = (lambda_val * lambda_val - x1 - x2) % self.p
        y_new = (lambda_val * (x1 - x_new) - y1) % self.p
        
        return (x_new, y_new)
    
    def mod_inverse(self, a, m):
        """Calcula el inverso modular usando el algoritmo extendido de Euclides"""
        if a < 0:
            a = (a % m + m) % m
        
        # Algoritmo extendido de Euclides
        def extended_gcd(a, b):
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y
        
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("El inverso modular no existe")
        
        return (x % m + m) % m
    
    def scalar_multiply(self, n, point):
        """
        Implementa el algoritmo Double and Add para multiplicación escalar
        Calcula [n]P
        """
        if n == 0:
            return None  # Punto en el infinito
        
        if n == 1:
            return point
        
        # Implementación del algoritmo Double and Add
        Q = point  # Q = P
        R = None   # R = O (punto en el infinito)
        
        print(f"🔢 Calculando [{n}]P usando Double and Add...")
        print(f"📍 Punto inicial P = {point}")
        
        step = 0
        while n > 0:
            step += 1
            print(f"  Step {step}: n = {n}")
            
            # Si n ≡ 1 mod 2, set R = R + Q
            if n % 2 == 1:
                R = self.point_add(R, Q)
                print(f"    n es impar, R = R + Q = {R}")
            
            # Set Q = [2]Q y n = ⌊n/2⌋
            Q = self.point_double(Q)
            n = n // 2
            
            print(f"    Q = 2Q = {Q}, n = {n}")
            
            if step > 20:  # Límite de pasos para evitar output excesivo
                print("    ... (continuando cálculo)")
                break
        
        # Continuar sin output si hay muchos pasos
        while n > 0:
            if n % 2 == 1:
                R = self.point_add(R, Q)
            Q = self.point_double(Q)
            n = n // 2
        
        print(f"✅ Resultado final: R = {R}")
        return R

def solve_cryptohack_elliptic():
    """Resuelve el desafío de curvas elípticas"""
    print("🎯 SOLUCIONADOR DE CURVAS ELÍPTICAS - CRYPTOHACK")
    print("=" * 50)
    
    # Parámetros del desafío
    # E: Y² = X³ + 497X + 1768 mod 9739
    a = 497
    b = 1768
    p = 9739
    
    # Punto P = (2339, 2213)
    P = (2339, 2213)
    
    # Escalar n = 7863
    n = 7863
    
    print(f"📋 Parámetros del desafío:")
    print(f"   Curva: Y² = X³ + {a}X + {b} mod {p}")
    print(f"   Punto P: {P}")
    print(f"   Escalar n: {n}")
    print(f"   Objetivo: Q = [{n}]P")
    print()
    
    # Crear la curva elíptica
    curve = EllipticCurve(a, b, p)
    
    # Verificar que P está en la curva
    print("🔍 Verificando que P está en la curva...")
    if curve.is_on_curve(P):
        print("✅ El punto P está en la curva")
    else:
        print("❌ El punto P NO está en la curva")
        return None
    
    # Verificar el caso de prueba: [1337]X = (1089, 6931) para X = (5323, 5438)
    print("\n🧪 Verificando caso de prueba...")
    X = (5323, 5438)
    expected = (1089, 6931)
    
    if curve.is_on_curve(X):
        print("✅ El punto X de prueba está en la curva")
        test_result = curve.scalar_multiply(1337, X)
        print(f"   [1337]X = {test_result}")
        print(f"   Esperado: {expected}")
        
        if test_result == expected:
            print("✅ Caso de prueba CORRECTO")
        else:
            print("❌ Caso de prueba FALLÓ")
    else:
        print("❌ El punto X de prueba NO está en la curva")
    
    # Calcular Q = [7863]P
    print(f"\n🚀 Calculando Q = [{n}]P...")
    Q = curve.scalar_multiply(n, P)
    
    if Q is None:
        print("❌ Error: Resultado es el punto en el infinito")
        return None
    
    print(f"✅ Resultado: Q = {Q}")
    
    # Verificar que Q está en la curva
    print("\n🔍 Verificando que Q está en la curva...")
    if curve.is_on_curve(Q):
        print("✅ El punto Q está en la curva")
    else:
        print("❌ ERROR: El punto Q NO está en la curva")
        return None
    
    # Generar la flag
    x, y = Q
    flag = f"crypto{{{x},{y}}}"
    
    print(f"\n🎉 ¡DESAFÍO RESUELTO!")
    print(f"🏆 FLAG: {flag}")
    
    # Guardar resultado
    solved_file = "challenges/solved/cryptohack_elliptic_solution.txt"
    with open(solved_file, 'w', encoding='utf-8') as f:
        f.write(f"Challenge: CryptoHack - Elliptic Curve Scalar Multiplication\n")
        f.write(f"Curve: Y² = X³ + {a}X + {b} mod {p}\n")
        f.write(f"Point P: {P}\n")
        f.write(f"Scalar n: {n}\n")
        f.write(f"Result Q = [n]P: {Q}\n")
        f.write(f"Verification: Point Q is on curve: {curve.is_on_curve(Q)}\n")
        f.write(f"FLAG: {flag}\n")
    
    print(f"💾 Solución guardada en: {solved_file}")
    
    return flag

if __name__ == "__main__":
    flag = solve_cryptohack_elliptic()
    
    if flag:
        print(f"\n🎯 RESUMEN:")
        print(f"   Desafío: Curvas Elípticas - Multiplicación Escalar")
        print(f"   Algoritmo: Double and Add")
        print(f"   Estado: ✅ RESUELTO")
        print(f"   Flag: {flag}")
    else:
        print("\n❌ No se pudo resolver el desafío")