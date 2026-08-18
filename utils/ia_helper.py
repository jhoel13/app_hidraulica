import re
import math
from typing import Dict, Any

class IAHelper:
    """Asistente IA para problemas hidráulicos"""
    
    def __init__(self):
        self.patrones = {
            'caudal': r'(caudal|Q|flujo|flow).*?(\d+\.?\d*)\s*(m3/s|lps|L/s|m³/s)',
            'velocidad': r'(velocidad|V).*?(\d+\.?\d*)\s*(m/s)',
            'diametro': r'(diámetro|diametro|D).*?(\d+\.?\d*)\s*(mm|cm|m)',
            'longitud': r'(longitud|L|largo).*?(\d+\.?\d*)\s*(m|km)',
            'pendiente': r'(pendiente|S|s).*?(\d+\.?\d*)\s*(%)',
            'presion': r'(presión|presion|P).*?(\d+\.?\d*)\s*(m|c.a.|kg/cm2|psi)'
        }
        
        self.conocimientos = {
            'manning': {
                'formula': 'Q = (1/n) * A * R^(2/3) * S^(1/2)',
                'descripcion': 'Ecuación de Manning para flujo uniforme en canales',
                'variables': {
                    'Q': 'Caudal (m³/s)',
                    'n': 'Coeficiente de rugosidad de Manning',
                    'A': 'Área hidráulica (m²)',
                    'R': 'Radio hidráulico (m)',
                    'S': 'Pendiente del canal (m/m)'
                }
            },
            'hazen_williams': {
                'formula': 'V = 0.849 * C * R^(0.63) * S^(0.54)',
                'descripcion': 'Ecuación de Hazen-Williams para tuberías',
                'variables': {
                    'V': 'Velocidad (m/s)',
                    'C': 'Coeficiente de Hazen-Williams',
                    'R': 'Radio hidráulico (m)',
                    'S': 'Pendiente de energía'
                }
            },
            'darcy_weisbach': {
                'formula': 'hf = f * (L/D) * (V²/2g)',
                'descripcion': 'Ecuación de Darcy-Weisbach para pérdidas de carga',
                'variables': {
                    'hf': 'Pérdida de carga (m)',
                    'f': 'Factor de fricción de Darcy',
                    'L': 'Longitud de la tubería (m)',
                    'D': 'Diámetro de la tubería (m)',
                    'V': 'Velocidad del fluido (m/s)',
                    'g': 'Aceleración de la gravedad (9.81 m/s²)'
                }
            },
            'reynolds': {
                'formula': 'Re = (V * D) / ν',
                'descripcion': 'Número de Reynolds para clasificar el régimen de flujo',
                'variables': {
                    'Re': 'Número de Reynolds (adimensional)',
                    'V': 'Velocidad (m/s)',
                    'D': 'Diámetro característico (m)',
                    'ν': 'Viscosidad cinemática (m²/s)'
                }
            }
        }
    
    def procesar_consulta(self, consulta: str) -> str:
        """Procesa una consulta en lenguaje natural"""
        consulta_lower = consulta.lower()
        
        # Detectar el tipo de problema
        if 'caudal' in consulta_lower or 'flujo' in consulta_lower:
            return self._resolver_caudal(consulta)
        elif 'tuber' in consulta_lower or 'pipeline' in consulta_lower:
            return self._resolver_tuberia(consulta)
        elif 'canal' in consulta_lower or 'channel' in consulta_lower:
            return self._resolver_canal(consulta)
        elif 'presión' in consulta_lower or 'presion' in consulta_lower:
            return self._resolver_presion(consulta)
        elif 'bombeo' in consulta_lower or 'bomb' in consulta_lower:
            return self._resolver_bombeo(consulta)
        elif 'perdida' in consulta_lower or 'pérdida' in consulta_lower:
            return self._resolver_perdidas(consulta)
        elif 'reynold' in consulta_lower:
            return self._explicar_concepto('reynolds')
        elif 'manning' in consulta_lower:
            return self._explicar_concepto('manning')
        elif 'darcy' in consulta_lower or 'weisbach' in consulta_lower:
            return self._explicar_concepto('darcy_weisbach')
        else:
            return self._respuesta_general(consulta)
    
    def _resolver_caudal(self, consulta: str) -> str:
        """Resuelve problemas de caudal"""
        # Extraer datos
        area = self._extraer_dato(consulta, r'área|area.*?(\d+\.?\d*)\s*(m2|m²)')
        velocidad = self._extraer_dato(consulta, r'velocidad.*?(\d+\.?\d*)\s*(m/s)')
        
        if area and velocidad:
            Q = area * velocidad
            return f"""
            <h3>✅ Solución para Cálculo de Caudal</h3>
            <p><strong>Datos:</strong></p>
            <ul>
                <li>Área: {area} m²</li>
                <li>Velocidad: {velocidad} m/s</li>
            </ul>
            <p><strong>Fórmula:</strong> Q = V × A</p>
            <p><strong>Cálculo:</strong></p>
            <ul>
                <li>Q = {velocidad} × {area}</li>
                <li><strong>Q = {Q:.3f} m³/s</strong></li>
                <li><strong>Q = {Q*1000:.1f} L/s</strong></li>
            </ul>
            <p>✅ <strong>Interpretación:</strong> El flujo es de {Q*1000:.1f} litros por segundo.</p>
            """
        
        return self._respuesta_general(consulta)
    
    def _resolver_tuberia(self, consulta: str) -> str:
        """Diseña tuberías"""
        caudal = self._extraer_dato(consulta, r'(\d+\.?\d*)\s*(L/s|lps|m3/s)')
        longitud = self._extraer_dato(consulta, r'(\d+\.?\d*)\s*(m|metros)')
        material = self._detectar_material(consulta)
        
        if caudal and longitud:
            Q = caudal / 1000 if 'L/s' in consulta else caudal
            V_recomendada = 1.5  # m/s
            D = math.sqrt(4 * Q / (math.pi * V_recomendada))
            
            # Diámetros comerciales
            diametros = [25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 200, 250]
            D_mm = D * 1000
            D_seleccionado = min(diametros, key=lambda x: abs(x - D_mm))
            
            return f"""
            <h3>✅ Diseño de Tubería para {caudal} L/s</h3>
            <p><strong>Datos de entrada:</strong></p>
            <ul>
                <li>Caudal: {caudal} L/s ({Q:.3f} m³/s)</li>
                <li>Longitud: {longitud} m</li>
                <li>Material: {material if material else 'No especificado'}</li>
            </ul>
            <p><strong>Cálculos:</strong></p>
            <ul>
                <li>Velocidad recomendada: {V_recomendada} m/s</li>
                <li>Diámetro calculado: {D*1000:.1f} mm</li>
                <li><strong>Diámetro comercial seleccionado: {D_seleccionado} mm</strong></li>
            </ul>
            <p><strong>Recomendación:</strong></p>
            <ul>
                <li>✅ Usar tubería de {D_seleccionado} mm de diámetro</li>
                <li>⚠️ Verificar presión de trabajo</li>
                <li>📝 Considerar pérdidas de carga</li>
            </ul>
            """
        
        return self._respuesta_general(consulta)
    
    def _explicar_concepto(self, concepto: str) -> str:
        """Explica conceptos hidráulicos"""
        if concepto in self.conocimientos:
            info = self.conocimientos[concepto]
            variables_html = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in info['variables'].items()])
            
            return f"""
            <h3>📚 Explicación: {concepto.replace('_', ' ').title()}</h3>
            <p><strong>Descripción:</strong> {info['descripcion']}</p>
            <p><strong>Fórmula:</strong> <code>{info['formula']}</code></p>
            <p><strong>Variables:</strong></p>
            <ul>{variables_html}</ul>
            <p><strong>Ejemplo de aplicación:</strong></p>
            <ul>
                <li>✅ Diseño de sistemas de agua potable</li>
                <li>✅ Cálculo de pérdidas en redes</li>
                <li>✅ Análisis de flujo en canales</li>
            </ul>
            """
        return "Concepto no encontrado en la base de conocimiento."
    
    def _respuesta_general(self, consulta: str) -> str:
        """Respuesta general cuando no se detecta un problema específico"""
        return """
        <h3>🤖 Asistente IA de Hidráulica</h3>
        <p>Puedo ayudarte con:</p>
        <ul>
            <li>✅ Cálculo de caudales</li>
            <li>✅ Diseño de tuberías</li>
            <li>✅ Diseño de canales</li>
            <li>✅ Cálculo de pérdidas de carga</li>
            <li>✅ Explicación de conceptos hidráulicos</li>
            <li>✅ Análisis de sistemas de bombeo</li>
            <li>✅ Diseño de estructuras hidráulicas</li>
        </ul>
        <p><strong>Ejemplos de preguntas:</strong></p>
        <ul>
            <li>"Calcula el caudal con área 2 m² y velocidad 3 m/s"</li>
            <li>"Diseña una tubería para 50 L/s en 800 metros"</li>
            <li>"Explica la ecuación de Manning"</li>
        </ul>
        """
    
    def _extraer_dato(self, texto: str, patron: str) -> float:
        """Extrae un dato numérico usando regex"""
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None
    
    def _detectar_material(self, texto: str) -> str:
        """Detecta el material de la tubería"""
        materiales = ['pvc', 'acero', 'concreto', 'hierro', 'cobre']
        for material in materiales:
            if material in texto.lower():
                return material
        return None
    
    def disenar_proyecto(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña un proyecto hidráulico completo"""
        tipo = datos.get('tipo', '')
        requerimientos = datos.get('requerimientos', {})
        
        if tipo == 'agua_potable':
            return self._disenar_agua_potable(requerimientos)
        elif tipo == 'alcantarillado':
            return self._disenar_alcantarillado(requerimientos)
        elif tipo == 'riego':
            return self._disenar_riego(requerimientos)
        else:
            return {'error': 'Tipo de proyecto no soportado'}
    
    def _disenar_agua_potable(self, req: Dict) -> Dict:
        """Diseño de sistema de agua potable"""
        poblacion = req.get('poblacion', 0)
        dotacion = req.get('dotacion', 150)  # L/hab/día
        
        Q_medio = poblacion * dotacion / 86400  # L/s
        Q_max = Q_medio * 1.2  # Factor de punta
        
        return {
            'tipo': 'Agua Potable',
            'poblacion': poblacion,
            'dotacion': dotacion,
            'caudal_medio': round(Q_medio, 2),
            'caudal_maximo': round(Q_max, 2),
            'recomendaciones': [
                'Tanque de almacenamiento: 1 día de consumo',
                'Red de distribución con diámetros comerciales',
                'Válvulas de control en puntos críticos'
            ]
        }