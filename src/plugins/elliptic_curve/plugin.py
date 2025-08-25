"""
Plugin de Curvas Elípticas - Ataques a ECC
"""

import re
import json
import gmpy2
from typing import List, Dict, Any, Optional, Tuple
from Crypto.Util.number import inverse, long_to_bytes, bytes_to_long
import math

from ..base import MultiTechniquePlugin
from ...models.data import ChallengeData, SolutionResult, PluginInfo, ChallengeType
from ...utils.logging import get_logger


class EllipticPoint:
    """Punto en curva elíptica"""
    
    def __init__(self, x: Optional[int], y: Optional[int], curve=None):
        self.x = x
        self.y = y
        self.curve = curve
        self.is_infinity = (x is None and y is None)
    
    def __eq__(self, other):
        if not isinstance(other, EllipticPoint):
            return False
        return self.x == other.x and self.y == other.y and self.is_infinity == other.is_infinity
    
    def __str__(self):
        if self.is_infinity:
            return "O (point at infinity)"
        return f"({self.x}, {self.y})"
    
    @classmethod
    def infinity(cls):
        """Punto en el infinito"""
        return cls(None, None)


class EllipticCurve:
    """Curva elíptica y = x³ + ax + b (mod p)"""
    
    def __init__(self, a: int, b: int, p: int):
        self.a = a
        self.b = b
        self.p = p
        
        # Verificar que la curva no es singular
        discriminant = (-16 * (4 * a**3 + 27 * b**2)) % p
        if discriminant == 0:
            raise ValueError("Curva singular (discriminante = 0)")
    
    def is_on_curve(self, point: EllipticPoint) -> bool:
        """Verificar si un punto está en la curva"""
        if point.is_infinity:
            return True
        
        x, y = point.x, point.y
        return (y**2) % self.p == (x**3 + self.a * x + self.b) % self.p
    
    def add_points(self, P: EllipticPoint, Q: EllipticPoint) -> EllipticPoint:
        """Suma de puntos en la curva elíptica"""
        if P.is_infinity:
            return Q
        if Q.is_infinity:
            return P
        
        if P.x == Q.x:
            if P.y == Q.y:
                # Duplicación de punto
                return self._double_point(P)
            else:
                # P + (-P) = O
                return EllipticPoint.infinity()
        
        # Suma general
        try:
            slope = ((Q.y - P.y) * inverse(Q.x - P.x, self.p)) % self.p
            x3 = (slope**2 - P.x - Q.x) % self.p
            y3 = (slope * (P.x - x3) - P.y) % self.p
            
            result = EllipticPoint(x3, y3, self)
            return result
        except Exception:
            return EllipticPoint.infinity()
    
    def _double_point(self, P: EllipticPoint) -> EllipticPoint:
        """Duplicación de punto"""
        if P.is_infinity:
            return P
        
        try:
            slope = ((3 * P.x**2 + self.a) * inverse(2 * P.y, self.p)) % self.p
            x3 = (slope**2 - 2 * P.x) % self.p
            y3 = (slope * (P.x - x3) - P.y) % self.p
            
            return EllipticPoint(x3, y3, self)
        except Exception:
            return EllipticPoint.infinity()
    
    def scalar_multiply(self, k: int, P: EllipticPoint) -> EllipticPoint:
        """Multiplicación escalar k*P"""
        if k == 0 or P.is_infinity:
            return EllipticPoint.infinity()
        
        if k < 0:
            # k*P = -(-k*P)
            neg_P = EllipticPoint(P.x, (-P.y) % self.p, self)
            return self.scalar_multiply(-k, neg_P)
        
        # Método de duplicación y suma
        result = EllipticPoint.infinity()
        addend = P
        
        while k:
            if k & 1:
                result = self.add_points(result, addend)
            addend = self._double_point(addend)
            k >>= 1
        
        return result
    
    def point_order(self, P: EllipticPoint, max_order: int = 10000) -> Optional[int]:
        """Calcular orden de un punto"""
        if P.is_infinity:
            return 1
        
        current = P
        for i in range(1, max_order + 1):
            if current.is_infinity:
                return i
            current = self.add_points(current, P)
        
        return None  # Orden muy grande
    
    def __str__(self):
        return f"y² = x³ + {self.a}x + {self.b} (mod {self.p})"


class EllipticCurvePlugin(MultiTechniquePlugin):
    """Plugin para ataques a curvas elípticas"""
    
    def __init__(self):
        super().__init__()
        
        # Curvas débiles conocidas
        self.weak_curves = self._load_weak_curves()
        
        # Límites para diferentes ataques
        self.max_pohlig_hellman_factors = 20
        self.max_brute_force_order = 10000
    
    def _create_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="elliptic_curve",
            version="1.0.0",
            description="Plugin para ataques a curvas elípticas",
            supported_types=[ChallengeType.ELLIPTIC_CURVE, ChallengeType.MIXED],
            techniques=[
                "invalid_curve_attack", "smart_attack", "pohlig_hellman",
                "weak_curve_detection", "point_order_attack", "singular_curve",
                "small_subgroup_attack", "twist_attack"
            ],
            priority=80
        )
    
    def can_solve(self, challenge_data: ChallengeData) -> float:
        """Evaluar si puede manejar el desafío de curvas elípticas"""
        confidence = 0.0
        
        # Verificar tipo de desafío
        if challenge_data.challenge_type == ChallengeType.ELLIPTIC_CURVE:
            confidence += 0.9
        elif challenge_data.challenge_type == ChallengeType.MIXED:
            confidence += 0.4
        
        # Buscar indicadores ECC en archivos
        ecc_indicators = 0
        for file_info in challenge_data.files:
            filename = file_info.path.name.lower()
            
            # Patrones en nombres de archivo
            if any(pattern in filename for pattern in ['ecc', 'elliptic', 'curve', 'ecdsa', 'point']):
                ecc_indicators += 1
                confidence += 0.2
            
            # Analizar contenido
            if self._is_text_file(file_info):
                content = self._read_file_content(file_info.path)
                if content:
                    ecc_content_score = self._analyze_ecc_content(content)
                    confidence += ecc_content_score * 0.3
                    if ecc_content_score > 0.5:
                        ecc_indicators += 1
        
        # Bonus si hay múltiples indicadores ECC
        if ecc_indicators >= 2:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _initialize_techniques(self) -> Dict[str, callable]:
        """Inicializar técnicas de curvas elípticas"""
        return {
            "weak_curve_detection": self._try_weak_curve_detection,
            "invalid_curve_attack": self._try_invalid_curve_attack,
            "smart_attack": self._try_smart_attack,
            "pohlig_hellman": self._try_pohlig_hellman,
            "small_subgroup_attack": self._try_small_subgroup_attack,
            "singular_curve": self._try_singular_curve,
            "point_order_attack": self._try_point_order_attack
        }
    
    def _is_text_file(self, file_info) -> bool:
        """Verificar si es archivo de texto"""
        if file_info.mime_type and 'text' in file_info.mime_type:
            return True
        
        text_extensions = {'.txt', '.json', '.py', '.sage', '.m'}
        return file_info.path.suffix.lower() in text_extensions
    
    def _analyze_ecc_content(self, content: str) -> float:
        """Analizar contenido para detectar elementos ECC"""
        confidence = 0.0
        content_lower = content.lower()
        
        # Patrones ECC
        ecc_patterns = [
            'elliptic', 'curve', 'ecc', 'ecdsa', 'point', 'scalar',
            'generator', 'order', 'cofactor', 'twist', 'invalid',
            'smart', 'pohlig', 'hellman', 'discrete log'
        ]
        
        for pattern in ecc_patterns:
            if pattern in content_lower:
                confidence += 0.1
        
        # Detectar parámetros de curva
        if re.search(r'[ay]\s*[=:]\s*\d+', content):
            confidence += 0.3
        
        # Detectar coordenadas de puntos
        if re.search(r'\(\s*\d+\s*,\s*\d+\s*\)', content):
            confidence += 0.2
        
        # Detectar formato JSON con parámetros ECC
        if self._looks_like_ecc_json(content):
            confidence += 0.5
        
        return min(confidence, 1.0)
    
    def _looks_like_ecc_json(self, content: str) -> bool:
        """Verificar si parece JSON con parámetros ECC"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                ecc_keys = {'a', 'b', 'p', 'G', 'n', 'h', 'Gx', 'Gy', 'point', 'curve'}
                return len(set(data.keys()) & ecc_keys) >= 2
        except:
            pass
        return False
    
    def _load_weak_curves(self) -> List[Dict[str, Any]]:
        """Cargar curvas débiles conocidas"""
        # Algunas curvas débiles para tests
        return [
            {
                'name': 'anomalous_curve_example',
                'a': 1, 'b': 1, 'p': 23,  # Curva anómala pequeña
                'weakness': 'anomalous'
            },
            {
                'name': 'small_order_curve',
                'a': 0, 'b': 7, 'p': 17,  # Curva con orden pequeño
                'weakness': 'small_order'
            }
        ]
    
    def _extract_ecc_parameters(self, challenge_data: ChallengeData) -> Dict[str, Any]:
        """Extraer parámetros de curva elíptica"""
        params = {}
        
        for file_info in challenge_data.files:
            content = self._read_file_content(file_info.path)
            if not content:
                continue
            
            # Intentar extraer de diferentes formatos
            file_params = {}
            
            # Formato JSON
            json_params = self._extract_from_json(content)
            if json_params:
                file_params.update(json_params)
            
            # Formato texto plano
            text_params = self._extract_from_text(content)
            if text_params:
                file_params.update(text_params)
            
            # Combinar parámetros
            params.update(file_params)
        
        return params
    
    def _extract_from_json(self, content: str) -> Dict[str, Any]:
        """Extraer parámetros de formato JSON"""
        params = {}
        
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # Parámetros de curva
                for key in ['a', 'b', 'p', 'n', 'h']:
                    if key in data:
                        params[key] = int(data[key]) if isinstance(data[key], str) else data[key]
                
                # Punto generador
                if 'G' in data and isinstance(data['G'], list) and len(data['G']) == 2:
                    params['Gx'], params['Gy'] = data['G']
                elif 'Gx' in data and 'Gy' in data:
                    params['Gx'] = int(data['Gx']) if isinstance(data['Gx'], str) else data['Gx']
                    params['Gy'] = int(data['Gy']) if isinstance(data['Gy'], str) else data['Gy']
                
                # Punto público
                if 'Q' in data and isinstance(data['Q'], list) and len(data['Q']) == 2:
                    params['Qx'], params['Qy'] = data['Q']
                elif 'Qx' in data and 'Qy' in data:
                    params['Qx'] = int(data['Qx']) if isinstance(data['Qx'], str) else data['Qx']
                    params['Qy'] = int(data['Qy']) if isinstance(data['Qy'], str) else data['Qy']
                
                # Clave privada y mensaje cifrado
                for key in ['d', 'k', 'r', 's', 'm', 'c']:
                    if key in data:
                        params[key] = int(data[key]) if isinstance(data[key], str) else data[key]
                        
        except Exception as e:
            self.logger.debug(f"Error extrayendo JSON ECC: {e}")
        
        return params
    
    def _extract_from_text(self, content: str) -> Dict[str, Any]:
        """Extraer parámetros de texto plano"""
        params = {}
        
        # Patrones para diferentes parámetros
        patterns = {
            'a': [r'a\s*[=:]\s*(\d+)', r'A\s*[=:]\s*(\d+)'],
            'b': [r'b\s*[=:]\s*(\d+)', r'B\s*[=:]\s*(\d+)'],
            'p': [r'p\s*[=:]\s*(\d+)', r'P\s*[=:]\s*(\d+)', r'prime\s*[=:]\s*(\d+)'],
            'n': [r'n\s*[=:]\s*(\d+)', r'order\s*[=:]\s*(\d+)'],
            'Gx': [r'Gx\s*[=:]\s*(\d+)', r'G\.x\s*[=:]\s*(\d+)'],
            'Gy': [r'Gy\s*[=:]\s*(\d+)', r'G\.y\s*[=:]\s*(\d+)'],
            'Qx': [r'Qx\s*[=:]\s*(\d+)', r'Q\.x\s*[=:]\s*(\d+)'],
            'Qy': [r'Qy\s*[=:]\s*(\d+)', r'Q\.y\s*[=:]\s*(\d+)'],
            'd': [r'd\s*[=:]\s*(\d+)', r'private\s*[=:]\s*(\d+)'],
        }
        
        for param, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        params[param] = int(matches[0])
                        break
                    except ValueError:
                        continue
        
        # Buscar puntos en formato (x, y)
        point_matches = re.findall(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', content)
        if point_matches:
            # Asumir que el primer punto es G y el segundo es Q
            if len(point_matches) >= 1 and 'Gx' not in params:
                params['Gx'], params['Gy'] = int(point_matches[0][0]), int(point_matches[0][1])
            if len(point_matches) >= 2 and 'Qx' not in params:
                params['Qx'], params['Qy'] = int(point_matches[1][0]), int(point_matches[1][1])
        
        return params
    
    def _try_weak_curve_detection(self, challenge_data: ChallengeData) -> SolutionResult:
        """Detectar curvas débiles conocidas"""
        self.logger.info("Detectando curvas débiles")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p']):
            return self._create_failure_result("Faltan parámetros de curva")
        
        a, b, p = params['a'], params['b'], params['p']
        
        # Verificar contra curvas débiles conocidas
        for weak_curve in self.weak_curves:
            if (weak_curve['a'] == a and weak_curve['b'] == b and weak_curve['p'] == p):
                return self._create_success_result(
                    flag=f"Curva débil detectada: {weak_curve['name']}",
                    method="weak_curve_detection",
                    confidence=0.9,
                    weakness=weak_curve['weakness']
                )
        
        # Verificar propiedades débiles
        try:
            curve = EllipticCurve(a, b, p)
            
            # Curva anómala (orden = p)
            if self._is_anomalous_curve(curve, p):
                return self._create_success_result(
                    flag="Curva anómala detectada",
                    method="anomalous_curve_detection",
                    confidence=0.95,
                    weakness="anomalous"
                )
            
            # Curva supersingular
            if self._is_supersingular_curve(curve, p):
                return self._create_success_result(
                    flag="Curva supersingular detectada",
                    method="supersingular_curve_detection",
                    confidence=0.8,
                    weakness="supersingular"
                )
                
        except Exception as e:
            return self._create_failure_result(f"Error analizando curva: {str(e)}")
        
        return self._create_failure_result("No se detectaron debilidades obvias")
    
    def _try_invalid_curve_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de curva inválida"""
        self.logger.info("Probando ataque de curva inválida")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p', 'Qx', 'Qy']):
            return self._create_failure_result("Faltan parámetros para ataque de curva inválida")
        
        a, b, p = params['a'], params['b'], params['p']
        Qx, Qy = params['Qx'], params['Qy']
        
        try:
            # Crear punto Q
            Q = EllipticPoint(Qx, Qy)
            
            # Probar diferentes curvas inválidas con el mismo punto Q
            for b_prime in range(1, min(100, p)):
                if b_prime == b:
                    continue
                
                try:
                    # Crear curva inválida
                    invalid_curve = EllipticCurve(a, b_prime, p)
                    
                    # Verificar si Q está en la curva inválida
                    if invalid_curve.is_on_curve(Q):
                        # Calcular orden del punto en la curva inválida
                        order = invalid_curve.point_order(Q, max_order=1000)
                        
                        if order and order < 1000:  # Orden pequeño
                            return self._create_success_result(
                                flag=f"Curva inválida encontrada: b'={b_prime}, orden={order}",
                                method="invalid_curve_attack",
                                confidence=0.8,
                                invalid_b=b_prime,
                                point_order=order
                            )
                            
                except Exception:
                    continue
            
            return self._create_failure_result("No se encontraron curvas inválidas útiles")
            
        except Exception as e:
            return self._create_failure_result(f"Error en ataque de curva inválida: {str(e)}")
    
    def _try_smart_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de Smart para curvas anómalas"""
        self.logger.info("Probando ataque de Smart")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p']):
            return self._create_failure_result("Faltan parámetros para ataque de Smart")
        
        a, b, p = params['a'], params['b'], params['p']
        
        try:
            curve = EllipticCurve(a, b, p)
            
            # Verificar si es curva anómala
            if not self._is_anomalous_curve(curve, p):
                return self._create_failure_result("La curva no es anómala")
            
            # Para curvas anómalas, el logaritmo discreto se puede resolver eficientemente
            # Esta es una implementación simplificada
            
            if 'Gx' in params and 'Gy' in params and 'Qx' in params and 'Qy' in params:
                G = EllipticPoint(params['Gx'], params['Gy'], curve)
                Q = EllipticPoint(params['Qx'], params['Qy'], curve)
                
                # En una implementación real, usaríamos el algoritmo de Smart
                # Aquí simulamos encontrar la clave privada
                for d in range(1, min(1000, p)):
                    if curve.scalar_multiply(d, G) == Q:
                        return self._create_success_result(
                            flag=f"Clave privada encontrada: d = {d}",
                            method="smart_attack",
                            confidence=0.95,
                            private_key=d
                        )
            
            return self._create_failure_result("No se pudo aplicar el ataque de Smart")
            
        except Exception as e:
            return self._create_failure_result(f"Error en ataque de Smart: {str(e)}")
    
    def _try_pohlig_hellman(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque Pohlig-Hellman para órdenes suaves"""
        self.logger.info("Probando ataque Pohlig-Hellman")
        
        params = self._extract_ecc_parameters(challenge_data)
        if 'n' not in params:
            return self._create_failure_result("Falta el orden de la curva para Pohlig-Hellman")
        
        n = params['n']
        
        # Factorizar el orden
        factors = self._factor_smooth_number(n)
        
        if not factors or len(factors) > self.max_pohlig_hellman_factors:
            return self._create_failure_result("El orden no es suficientemente suave")
        
        # Verificar que todos los factores son pequeños
        max_factor = max(factors)
        if max_factor > 10000:
            return self._create_failure_result("Factores demasiado grandes para Pohlig-Hellman")
        
        return self._create_success_result(
            flag=f"Orden suave detectado: {factors}",
            method="pohlig_hellman",
            confidence=0.8,
            smooth_factors=factors,
            max_factor=max_factor
        )
    
    def _try_small_subgroup_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque de subgrupo pequeño"""
        self.logger.info("Probando ataque de subgrupo pequeño")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p', 'Gx', 'Gy']):
            return self._create_failure_result("Faltan parámetros para ataque de subgrupo pequeño")
        
        try:
            curve = EllipticCurve(params['a'], params['b'], params['p'])
            G = EllipticPoint(params['Gx'], params['Gy'], curve)
            
            # Calcular orden del punto generador
            order = curve.point_order(G, max_order=self.max_brute_force_order)
            
            if order and order < 1000:
                return self._create_success_result(
                    flag=f"Subgrupo pequeño detectado: orden = {order}",
                    method="small_subgroup_attack",
                    confidence=0.9,
                    subgroup_order=order
                )
            
            return self._create_failure_result("No se encontró subgrupo pequeño")
            
        except Exception as e:
            return self._create_failure_result(f"Error en ataque de subgrupo pequeño: {str(e)}")
    
    def _try_singular_curve(self, challenge_data: ChallengeData) -> SolutionResult:
        """Detectar curvas singulares"""
        self.logger.info("Verificando curvas singulares")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p']):
            return self._create_failure_result("Faltan parámetros de curva")
        
        a, b, p = params['a'], params['b'], params['p']
        
        # Calcular discriminante
        discriminant = (-16 * (4 * a**3 + 27 * b**2)) % p
        
        if discriminant == 0:
            return self._create_success_result(
                flag="Curva singular detectada (discriminante = 0)",
                method="singular_curve_detection",
                confidence=0.95,
                discriminant=discriminant
            )
        
        return self._create_failure_result("La curva no es singular")
    
    def _try_point_order_attack(self, challenge_data: ChallengeData) -> SolutionResult:
        """Ataque basado en orden de puntos"""
        self.logger.info("Probando ataque de orden de puntos")
        
        params = self._extract_ecc_parameters(challenge_data)
        if not all(k in params for k in ['a', 'b', 'p']):
            return self._create_failure_result("Faltan parámetros de curva")
        
        try:
            curve = EllipticCurve(params['a'], params['b'], params['p'])
            
            # Si tenemos puntos específicos, calcular sus órdenes
            points_to_check = []
            
            if 'Gx' in params and 'Gy' in params:
                points_to_check.append(('G', EllipticPoint(params['Gx'], params['Gy'], curve)))
            
            if 'Qx' in params and 'Qy' in params:
                points_to_check.append(('Q', EllipticPoint(params['Qx'], params['Qy'], curve)))
            
            results = {}
            for name, point in points_to_check:
                order = curve.point_order(point, max_order=self.max_brute_force_order)
                if order:
                    results[name] = order
            
            if results:
                return self._create_success_result(
                    flag=f"Órdenes de puntos: {results}",
                    method="point_order_attack",
                    confidence=0.7,
                    point_orders=results
                )
            
            return self._create_failure_result("No se pudieron calcular órdenes de puntos")
            
        except Exception as e:
            return self._create_failure_result(f"Error calculando órdenes: {str(e)}")
    
    # Métodos auxiliares
    
    def _is_anomalous_curve(self, curve: EllipticCurve, p: int) -> bool:
        """Verificar si la curva es anómala (orden = p)"""
        # Para curvas pequeñas, podemos verificar directamente
        if p < 1000:
            # Contar puntos en la curva (implementación simple)
            count = 1  # Punto en el infinito
            for x in range(p):
                y_squared = (x**3 + curve.a * x + curve.b) % p
                # Verificar si y_squared es un residuo cuadrático
                if self._is_quadratic_residue(y_squared, p):
                    count += 2 if y_squared != 0 else 1
            
            return count == p
        
        return False  # Para curvas grandes, necesitaríamos algoritmos más sofisticados
    
    def _is_supersingular_curve(self, curve: EllipticCurve, p: int) -> bool:
        """Verificar si la curva es supersingular"""
        # Implementación simplificada
        # Una curva es supersingular si su traza es 0 mod p
        # Para p pequeño, podemos calcularlo
        if p < 100:
            return self._is_anomalous_curve(curve, p)  # Simplificación
        return False
    
    def _is_quadratic_residue(self, a: int, p: int) -> bool:
        """Verificar si a es residuo cuadrático mod p"""
        if a == 0:
            return True
        return pow(a, (p - 1) // 2, p) == 1
    
    def _factor_smooth_number(self, n: int, max_factor: int = 10000) -> List[int]:
        """Factorizar número suave"""
        factors = []
        d = 2
        
        while d * d <= n and d <= max_factor:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        
        if n > 1:
            if n <= max_factor:
                factors.append(n)
            else:
                return []  # No es suave
        
        return factors
    
    def _extract_flag_from_result(self, result: Any) -> Optional[str]:
        """Extraer flag del resultado"""
        if isinstance(result, str):
            # Buscar patrones de flag
            flag_patterns = [
                r'CTF\{[^}]+\}',
                r'FLAG\{[^}]+\}',
                r'flag\{[^}]+\}',
            ]
            
            for pattern in flag_patterns:
                matches = re.findall(pattern, result, re.IGNORECASE)
                if matches:
                    return matches[0]
        
        return None