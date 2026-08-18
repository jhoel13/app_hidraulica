import math
import numpy as np
from scipy.optimize import fsolve

def calcular_caudal(area, velocidad):
    """Q = V * A"""
    Q = area * velocidad
    return {
        'caudal': round(Q, 4),
        'area': round(area, 4),
        'velocidad': round(velocidad, 4),
        'unidades': 'm³/s'
    }

def calcular_reynolds(velocidad, diametro, viscosidad=0.000001):
    """Re = V * D / ν"""
    Re = (velocidad * diametro) / viscosidad
    tipo = 'Turbulento' if Re > 4000 else 'Laminar' if Re < 2000 else 'Transición'
    
    return {
        'reynolds': round(Re, 0),
        'tipo': tipo,
        'velocidad': round(velocidad, 4),
        'diametro': round(diametro, 4),
        'viscosidad': viscosidad
    }

def factor_friccion(Re, rugosidad_relativa):
    """Ecuación de Colebrook-White"""
    if Re <= 2000:
        f = 64 / Re
    else:
        # Método iterativo de Newton
        def colebrook(f):
            return -2 * math.log10((rugosidad_relativa / 3.7) + (2.51 / (Re * math.sqrt(f)))) - 1 / math.sqrt(f)
        
        f = fsolve(colebrook, 0.02)[0]
    
    return round(f, 6)

def calcular_perdidas_carga(Q, D, L, rugosidad=0.00015):
    """Fórmula de Darcy-Weisbach"""
    A = math.pi * (D ** 2) / 4
    V = Q / A
    
    # Calcular Reynolds
    nu = 1e-6  # viscosidad cinemática del agua a 20°C
    Re = (V * D) / nu
    
    # Rugosidad relativa
    rug_rel = rugosidad / D
    
    # Factor de fricción
    f = factor_friccion(Re, rug_rel)
    
    # Pérdida por fricción
    hf = f * (L / D) * (V ** 2) / (2 * 9.81)
    
    # Pérdidas menores (aproximación)
    hm = 0.1 * hf  # Asumiendo 10% de pérdidas menores
    
    return {
        'velocidad': round(V, 4),
        'reynolds': round(Re, 0),
        'factor_friccion': f,
        'perdida_friccion': round(hf, 4),
        'perdida_menor': round(hm, 4),
        'perdida_total': round(hf + hm, 4),
        'unidades': 'm'
    }

def disenar_canal(Q, S, n, tipo='trapezoidal'):
    """Diseño de canales usando la ecuación de Manning"""
    # Manning: Q = (1/n) * A * R^(2/3) * S^(1/2)
    
    if tipo == 'trapezoidal':
        # Canal trapezoidal optimizado
        # Asumiendo base (b) y tirante (y) con talud z=1
        z = 1
        y = (Q * n / (S ** 0.5)) ** 0.6  # Estimación inicial
        
        def area(y):
            return (b + z * y) * y
        
        def perimetro(y):
            return b + 2 * y * math.sqrt(1 + z**2)
        
        # Optimizar para sección hidráulica más eficiente
        b = 2 * y * (math.sqrt(1 + z**2) - z)
        
        A = (b + z * y) * y
        P = b + 2 * y * math.sqrt(1 + z**2)
        R = A / P
        
        # Verificar caudal
        Q_calc = (1/n) * A * (R ** (2/3)) * (S ** 0.5)
        
        return {
            'tipo': 'Trapezoidal',
            'base': round(b, 3),
            'tirante': round(y, 3),
            'area': round(A, 3),
            'perimetro': round(P, 3),
            'radio_hidraulico': round(R, 3),
            'caudal_calculado': round(Q_calc, 4),
            'pendiente': S,
            'rugosidad': n,
            'unidades': 'm'
        }
    
    elif tipo == 'rectangular':
        # Canal rectangular
        y = (Q * n / (S ** 0.5)) ** 0.6
        b = Q / (y * (S ** 0.5) / n)
        
        A = b * y
        P = b + 2 * y
        R = A / P
        Q_calc = (1/n) * A * (R ** (2/3)) * (S ** 0.5)
        
        return {
            'tipo': 'Rectangular',
            'base': round(b, 3),
            'tirante': round(y, 3),
            'area': round(A, 3),
            'perimetro': round(P, 3),
            'radio_hidraulico': round(R, 3),
            'caudal_calculado': round(Q_calc, 4),
            'pendiente': S,
            'rugosidad': n,
            'unidades': 'm'
        }
    
    elif tipo == 'circular':
        # Canal circular (alcantarilla)
        D = (Q * n / (S ** 0.5)) ** 0.6
        y = 0.8 * D  # Tirante al 80% de llenado
        
        A = (D ** 2 / 8) * (2 * math.acos(1 - 2*y/D) - math.sin(2 * math.acos(1 - 2*y/D)))
        P = D * math.acos(1 - 2*y/D)
        R = A / P
        
        return {
            'tipo': 'Circular',
            'diametro': round(D, 3),
            'tirante': round(y, 3),
            'area': round(A, 3),
            'perimetro': round(P, 3),
            'radio_hidraulico': round(R, 3),
            'unidades': 'm'
        }

def disenar_tuberia(Q, L, D=0, material='pvc', tipo='completo'):
    """Diseño completo de tubería"""
    # Velocidad recomendada: 0.5 - 3 m/s
    V_recomendada = 1.5
    
    if D == 0:
        # Calcular diámetro requerido
        A_requerida = Q / V_recomendada
        D_calc = math.sqrt(4 * A_requerida / math.pi)
        
        # Diámetros comerciales (PVC, en mm)
        diametros_comerciales = [25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 200, 250, 315]
        D_mm = D_calc * 1000
        
        # Seleccionar el diámetro comercial más cercano
        D_seleccionado = min(diametros_comerciales, key=lambda x: abs(x - D_mm))
        D = D_seleccionado / 1000  # Convertir a metros
        
        # Rugosidad según material
        rugosidades = {
            'pvc': 0.0000015,
            'acero': 0.000045,
            'concreto': 0.0003,
            'hierro': 0.00015
        }
        
        rugosidad = rugosidades.get(material, 0.00015)
        
        # Calcular pérdidas
        perdidas = calcular_perdidas_carga(Q, D, L, rugosidad)
        
        if tipo == 'completo':
            # Calcular velocidad real
            A_real = math.pi * (D ** 2) / 4
            V_real = Q / A_real
            
            return {
                'diámetro_seleccionado': D_seleccionado,
                'diámetro_m': round(D, 4),
                'velocidad': round(V_real, 3),
                'área': round(A_real, 4),
                'material': material,
                'pérdidas': perdidas,
                'recomendaciones': 'Velocidad adecuada' if 0.5 <= V_real <= 3 else 'Revisar velocidad'
            }
    
    return {'error': 'No se pudo diseñar la tubería'}

def metodo_racional(C, i, A):
    """Q = C * i * A / 360 (SI)"""
    Q = C * i * A / 360
    return {
        'caudal': round(Q, 3),
        'coeficiente': C,
        'intensidad': round(i, 2),
        'area': round(A, 2),
        'unidades': 'm³/s'
    }

def hidrograma_unitario(t, Tp, Qp):
    """Hidrograma unitario sintético"""
    tp = Tp
    qp = Qp
    tr = 1.67 * tp  # Duración de la lluvia
    
    # Puntos del hidrograma (t en horas, Q en m³/s)
    tiempos = np.arange(0, 10 * tp, 0.1)
    caudales = []
    
    for t in tiempos:
        if t <= tr:
            q = qp * (t / tp) * np.exp(1 - t/tp)
        else:
            q = qp * np.exp(-0.5 * ((t - tp) / (0.5 * tp)) ** 2)
        caudales.append(q)
    
    return {
        'tiempos': tiempos.tolist(),
        'caudales': caudales,
        'tp': tp,
        'qp': qp,
        'tr': tr
    }