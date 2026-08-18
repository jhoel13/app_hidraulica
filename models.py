from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

# ============================================
# MODELOS PRINCIPALES
# ============================================

class Usuario(UserMixin, db.Model):
    """Modelo de usuarios del sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    codigo_estudiante = db.Column(db.String(20), unique=True, index=True)
    carrera = db.Column(db.String(50))
    password_hash = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    es_activo = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='estudiante')
    avatar = db.Column(db.String(200))
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(200))
    
    # Relaciones
    portafolios = db.relationship('Portafolio', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    calculos = db.relationship('CalculoHistorico', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    proyectos = db.relationship('Proyecto', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    documentos = db.relationship('Documento', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    consultas_ia = db.relationship('ConsultaIA', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    favoritos = db.relationship('Favorito', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    sesiones = db.relationship('SesionUsuario', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
    
    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'
    
    @property
    def es_admin(self):
        return self.role == 'admin'
    
    @property
    def es_profesor(self):
        return self.role in ['admin', 'profesor']
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas del usuario"""
        return {
            'total_calculos': self.calculos.count(),
            'total_portafolios': self.portafolios.count(),
            'total_proyectos': self.proyectos.count(),
            'total_consultas_ia': self.consultas_ia.count(),
            'ultimo_acceso': self.ultimo_acceso.strftime('%d/%m/%Y %H:%M') if self.ultimo_acceso else 'Nunca'
        }


class Portafolio(db.Model):
    """Modelo de portafolios de usuarios"""
    __tablename__ = 'portafolios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    archivo_path = db.Column(db.String(500))
    tipo_archivo = db.Column(db.String(50))
    tamano_archivo = db.Column(db.Integer)  # En bytes
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    es_publico = db.Column(db.Boolean, default=True)
    categoria = db.Column(db.String(50))
    tags = db.Column(db.String(200))  # Tags separados por comas
    vistas = db.Column(db.Integer, default=0)
    descargas = db.Column(db.Integer, default=0)
    
    # Relaciones
    comentarios = db.relationship('ComentarioPortafolio', backref='portafolio', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Portafolio {self.titulo}>'
    
    @property
    def tamaño_formateado(self):
        if self.tamano_archivo:
            for unidad in ['B', 'KB', 'MB', 'GB']:
                if self.tamano_archivo < 1024:
                    return f'{self.tamano_archivo:.1f} {unidad}'
                self.tamano_archivo /= 1024
        return '0 B'
    
    @property
    def tags_list(self):
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    def incrementar_vista(self):
        self.vistas += 1
        db.session.commit()
    
    def incrementar_descarga(self):
        self.descargas += 1
        db.session.commit()


class CalculoHistorico(db.Model):
    """Modelo de cálculos históricos realizados por usuarios"""
    __tablename__ = 'calculos_historicos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    tipo_calculo = db.Column(db.String(50), nullable=False)
    subtipo = db.Column(db.String(50))
    datos_entrada = db.Column(db.JSON)
    resultados = db.Column(db.JSON)
    grafico_base64 = db.Column(db.Text)  # Gráfico generado en base64
    pdf_generado = db.Column(db.String(500))
    fecha_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    tiempo_ejecucion = db.Column(db.Float)  # En segundos
    es_favorito = db.Column(db.Boolean, default=False)
    notas = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Calculo {self.tipo_calculo} - {self.fecha_calculo}>'
    
    @property
    def resumen(self):
        """Resumen del cálculo para mostrar en listas"""
        resumen = {
            'caudal': 'Cálculo de Caudal',
            'canal': 'Diseño de Canal',
            'tuberia': 'Diseño de Tubería',
            'perdidas': 'Pérdidas de Carga',
            'reynolds': 'Número de Reynolds',
            'friccion': 'Factor de Fricción',
            'manning': 'Ecuación de Manning',
            'hazen': 'Hazen-Williams',
            'bernoulli': 'Ecuación de Bernoulli',
            'racional': 'Método Racional',
            'hidrograma': 'Hidrograma',
            'idf': 'Curva IDF',
            'presa': 'Diseño de Presa',
            'ia_consulta': 'Consulta IA'
        }
        return resumen.get(self.tipo_calculo, self.tipo_calculo)
    
    def obtener_grafico(self):
        """Devuelve el gráfico como imagen HTML si existe"""
        if self.grafico_base64:
            return f'<img src="data:image/png;base64,{self.grafico_base64}" alt="Gráfico">'
        return None


class Proyecto(db.Model):
    """Modelo de proyectos hidráulicos"""
    __tablename__ = 'proyectos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='borrador')  # borrador, activo, completado, archivado
    datos = db.Column(db.JSON)
    resultados = db.Column(db.JSON)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_completado = db.Column(db.DateTime)
    archivo_inp = db.Column(db.String(500))  # Archivo EPANET
    archivo_pdf = db.Column(db.String(500))
    es_publico = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Proyecto {self.nombre}>'
    
    @property
    def estado_color(self):
        colores = {
            'borrador': '#6b7280',
            'activo': '#2563eb',
            'completado': '#16a34a',
            'archivado': '#dc2626'
        }
        return colores.get(self.estado, '#6b7280')
    
    @property
    def estado_icono(self):
        iconos = {
            'borrador': '📝',
            'activo': '🔄',
            'completado': '✅',
            'archivado': '📦'
        }
        return iconos.get(self.estado, '📝')


class Documento(db.Model):
    """Modelo de documentos subidos a la biblioteca"""
    __tablename__ = 'documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    archivo_path = db.Column(db.String(500))
    tipo_archivo = db.Column(db.String(50))
    tamano_archivo = db.Column(db.Integer)
    categoria = db.Column(db.String(50))
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_procesamiento = db.Column(db.DateTime)
    contenido_extraido = db.Column(db.Text)  # Texto extraído del documento
    palabras_clave = db.Column(db.String(500))
    es_publico = db.Column(db.Boolean, default=True)
    descargas = db.Column(db.Integer, default=0)
    
    # Relaciones
    consultas = db.relationship('ConsultaDocumento', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Documento {self.titulo}>'


class ConsultaIA(db.Model):
    """Modelo de consultas al asistente IA"""
    __tablename__ = 'consultas_ia'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    pregunta = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # calculo, explicacion, diseno, etc.
    contexto = db.Column(db.JSON)  # Datos adicionales del contexto
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow)
    tiempo_respuesta = db.Column(db.Float)
    es_favorito = db.Column(db.Boolean, default=False)
    valoracion = db.Column(db.Integer)  # 1-5
    
    def __repr__(self):
        return f'<ConsultaIA {self.id} - {self.fecha_consulta}>'


class ConsultaDocumento(db.Model):
    """Modelo de consultas a documentos"""
    __tablename__ = 'consultas_documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    pregunta = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text)
    fragmento_referencia = db.Column(db.Text)  # Fragmento del documento usado
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConsultaDocumento {self.id}>'


class ComentarioPortafolio(db.Model):
    """Modelo de comentarios en portafolios"""
    __tablename__ = 'comentarios_portafolio'
    
    id = db.Column(db.Integer, primary_key=True)
    portafolio_id = db.Column(db.Integer, db.ForeignKey('portafolios.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    fecha_comentario = db.Column(db.DateTime, default=datetime.utcnow)
    es_edicion = db.Column(db.Boolean, default=False)
    fecha_edicion = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Comentario {self.id} - {self.fecha_comentario}>'


class Notificacion(db.Model):
    """Modelo de notificaciones del sistema"""
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(30))  # info, success, warning, error
    link = db.Column(db.String(200))
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Notificacion {self.titulo}>'
    
    def marcar_leida(self):
        self.leida = True
        self.fecha_lectura = datetime.utcnow()
        db.session.commit()


class Favorito(db.Model):
    """Modelo de favoritos del usuario"""
    __tablename__ = 'favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # calculo, proyecto, documento, etc.
    item_id = db.Column(db.Integer, nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.String(200))
    
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'tipo', 'item_id', name='unique_favorito'),
    )
    
    def __repr__(self):
        return f'<Favorito {self.tipo}-{self.item_id}>'


class SesionUsuario(db.Model):
    """Modelo de sesiones de usuario"""
    __tablename__ = 'sesiones_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(200), unique=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    fecha_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime)
    es_activa = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Sesion {self.id} - {self.fecha_inicio}>'
    
    def cerrar_sesion(self):
        self.fecha_fin = datetime.utcnow()
        self.es_activa = False
        db.session.commit()


# ============================================
# MODELOS PARA EL SISTEMA DE RÍOS
# ============================================

class EstacionMonitoreo(db.Model):
    """Modelo de estaciones de monitoreo de ríos"""
    __tablename__ = 'estaciones_monitoreo'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    rio = db.Column(db.String(100))
    ubicacion = db.Column(db.String(200))
    activa = db.Column(db.Boolean, default=True)
    fecha_instalacion = db.Column(db.DateTime)
    
    # Relaciones
    mediciones = db.relationship('MedicionRio', backref='estacion', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Estacion {self.nombre}>'
    
    @property
    def ultima_medicion(self):
        return self.mediciones.order_by(MedicionRio.fecha_medicion.desc()).first()


class MedicionRio(db.Model):
    """Modelo de mediciones de ríos"""
    __tablename__ = 'mediciones_rios'
    
    id = db.Column(db.Integer, primary_key=True)
    estacion_id = db.Column(db.Integer, db.ForeignKey('estaciones_monitoreo.id', ondelete='CASCADE'), nullable=False)
    caudal = db.Column(db.Float)  # m³/s
    nivel = db.Column(db.Float)  # m
    temperatura = db.Column(db.Float)  # °C
    lluvia = db.Column(db.Float)  # mm/h
    velocidad = db.Column(db.Float)  # m/s
    ph = db.Column(db.Float)
    oxigeno_disuelto = db.Column(db.Float)  # mg/L
    turbidez = db.Column(db.Float)  # NTU
    riesgo = db.Column(db.String(20))  # bajo, medio, alto
    fecha_medicion = db.Column(db.DateTime, default=datetime.utcnow)
    es_simulada = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Medicion {self.fecha_medicion} - {self.estacion.nombre}>'
    
    @property
    def riesgo_color(self):
        colores = {
            'bajo': '#22c55e',
            'medio': '#eab308',
            'alto': '#ef4444'
        }
        return colores.get(self.riesgo, '#6b7280')


# ============================================
# MODELOS PARA EL SISTEMA DE REDES
# ============================================

class RedHidraulica(db.Model):
    """Modelo de redes hidráulicas"""
    __tablename__ = 'redes_hidraulicas'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id', ondelete='CASCADE'))
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50))  # agua_potable, riego, alcantarillado
    datos_json = db.Column(db.JSON)  # Datos completos de la red
    archivo_inp = db.Column(db.String(500))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    nodos = db.relationship('NodoRed', backref='red', lazy='dynamic', cascade='all, delete-orphan')
    tuberias = db.relationship('TuberiaRed', backref='red', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Red {self.nombre}>'


class NodoRed(db.Model):
    """Modelo de nodos en una red hidráulica"""
    __tablename__ = 'nodos_red'
    
    id = db.Column(db.Integer, primary_key=True)
    red_id = db.Column(db.Integer, db.ForeignKey('redes_hidraulicas.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(50))
    x = db.Column(db.Float)  # Coordenada X en el canvas
    y = db.Column(db.Float)  # Coordenada Y en el canvas
    cota = db.Column(db.Float)  # m
    demanda = db.Column(db.Float)  # L/s
    presion = db.Column(db.Float)  # m
    tipo = db.Column(db.String(20), default='junction')  # junction, reservoir, tank
    
    def __repr__(self):
        return f'<Nodo {self.nombre}>'


class TuberiaRed(db.Model):
    """Modelo de tuberías en una red hidráulica"""
    __tablename__ = 'tuberias_red'
    
    id = db.Column(db.Integer, primary_key=True)
    red_id = db.Column(db.Integer, db.ForeignKey('redes_hidraulicas.id', ondelete='CASCADE'), nullable=False)
    nodo_inicio_id = db.Column(db.Integer, db.ForeignKey('nodos_red.id', ondelete='CASCADE'), nullable=False)
    nodo_fin_id = db.Column(db.Integer, db.ForeignKey('nodos_red.id', ondelete='CASCADE'), nullable=False)
    diametro = db.Column(db.Float)  # m
    longitud = db.Column(db.Float)  # m
    rugosidad = db.Column(db.Float)  # m
    caudal = db.Column(db.Float)  # m³/s
    velocidad = db.Column(db.Float)  # m/s
    perdida = db.Column(db.Float)  # m
    
    # Relaciones
    nodo_inicio = db.relationship('NodoRed', foreign_keys=[nodo_inicio_id])
    nodo_fin = db.relationship('NodoRed', foreign_keys=[nodo_fin_id])
    
    def __repr__(self):
        return f'<Tuberia {self.id}>'


# ============================================
# MODELOS PARA EL SISTEMA DE INUNDACIONES
# ============================================

class ZonaInundacion(db.Model):
    """Modelo de zonas de inundación"""
    __tablename__ = 'zonas_inundacion'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    distrito = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    riesgo = db.Column(db.String(20))  # bajo, medio, alto
    coordenadas = db.Column(db.JSON)  # Polígono de la zona
    area = db.Column(db.Float)  # ha
    poblacion_afectada = db.Column(db.Integer)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    eventos = db.relationship('EventoInundacion', backref='zona', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Zona {self.nombre}>'


class EventoInundacion(db.Model):
    """Modelo de eventos de inundación"""
    __tablename__ = 'eventos_inundacion'
    
    id = db.Column(db.Integer, primary_key=True)
    zona_id = db.Column(db.Integer, db.ForeignKey('zonas_inundacion.id', ondelete='CASCADE'), nullable=False)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    severidad = db.Column(db.String(20))  # leve, moderada, grave
    descripcion = db.Column(db.Text)
    caudal_estimado = db.Column(db.Float)  # m³/s
    nivel_agua = db.Column(db.Float)  # m
    area_afectada = db.Column(db.Float)  # ha
    viviendas_afectadas = db.Column(db.Integer)
    personas_afectadas = db.Column(db.Integer)
    danos_estimados = db.Column(db.Float)  # S/.
    fuente = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Evento {self.fecha_evento}>'


# ============================================
# MODELOS PARA EL SISTEMA DE PRESAS
# ============================================

class DisenoPresa(db.Model):
    """Modelo de diseños de presas"""
    __tablename__ = 'disenos_presa'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id', ondelete='CASCADE'))
    nombre = db.Column(db.String(200), nullable=False)
    altura = db.Column(db.Float)  # m
    ancho_corona = db.Column(db.Float)  # m
    ancho_base = db.Column(db.Float)  # m
    material = db.Column(db.String(50))
    empuje_hidrostatico = db.Column(db.Float)  # kN
    peso_presa = db.Column(db.Float)  # kN
    fs_vuelco = db.Column(db.Float)  # Factor de seguridad al vuelco
    fs_deslizamiento = db.Column(db.Float)  # Factor de seguridad al deslizamiento
    estado = db.Column(db.String(20))  # estable, inestable
    datos_json = db.Column(db.JSON)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DisenoPresa {self.nombre}>'


# ============================================
# MODELOS DE AUDITORÍA
# ============================================

class LogAuditoria(db.Model):
    """Modelo de logs de auditoría"""
    __tablename__ = 'logs_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True)
    accion = db.Column(db.String(50), nullable=False)
    tabla = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    datos_anteriores = db.Column(db.JSON)
    datos_nuevos = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    fecha_accion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Log {self.accion} - {self.fecha_accion}>'


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def init_db():
    """Inicializa la base de datos con datos de ejemplo"""
    # Crear usuario admin si no existe
    admin = Usuario.query.filter_by(email='admin@unc.edu.pe').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = Usuario(
            email='admin@unc.edu.pe',
            nombre='Administrador',
            apellido='UNC',
            codigo_estudiante='ADMIN001',
            carrera='Ingeniería Hidráulica',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            es_activo=True
        )
        db.session.add(admin)
        db.session.commit()
    
    # Crear algunas estaciones de monitoreo
    if EstacionMonitoreo.query.count() == 0:
        estaciones = [
            EstacionMonitoreo(
                nombre='Río Cajamarca',
                descripcion='Estación principal del río Cajamarca',
                latitud=-7.1633,
                longitud=-78.5000,
                rio='Cajamarca',
                ubicacion='Cajamarca',
                activa=True
            ),
            EstacionMonitoreo(
                nombre='Río Chonta',
                descripcion='Estación del río Chonta',
                latitud=-7.1500,
                longitud=-78.5200,
                rio='Chonta',
                ubicacion='Cajamarca',
                activa=True
            ),
            EstacionMonitoreo(
                nombre='Río Mashcón',
                descripcion='Estación del río Mashcón',
                latitud=-7.1800,
                longitud=-78.4800,
                rio='Mashcón',
                ubicacion='Cajamarca',
                activa=True
            )
        ]
        for estacion in estaciones:
            db.session.add(estacion)
        db.session.commit()
        
        # Agregar mediciones simuladas
        for estacion in estaciones:
            for _ in range(10):
                medicion = MedicionRio(
                    estacion_id=estacion.id,
                    caudal=5 + (estacion.id * 3) + (__import__('random').random() * 5),
                    nivel=1.5 + (estacion.id * 0.5) + (__import__('random').random() * 0.5),
                    temperatura=16 + (__import__('random').random() * 4),
                    lluvia=__import__('random').random() * 10,
                    velocidad=0.5 + (__import__('random').random() * 0.5),
                    fecha_medicion=datetime.utcnow() - __import__('datetime').timedelta(hours=__import__('random').randint(1, 24))
                )
                db.session.add(medicion)
        db.session.commit()
    
    return 'Base de datos inicializada correctamente'


# ============================================
# FUNCIONES DE CONSULTA
# ============================================

def obtener_estadisticas_generales():
    """Obtiene estadísticas generales del sistema"""
    return {
        'total_usuarios': Usuario.query.count(),
        'total_portafolios': Portafolio.query.count(),
        'total_calculos': CalculoHistorico.query.count(),
        'total_proyectos': Proyecto.query.count(),
        'total_documentos': Documento.query.count(),
        'total_consultas_ia': ConsultaIA.query.count(),
        'total_mediciones': MedicionRio.query.count()
    }


def obtener_actividad_reciente(limite=10):
    """Obtiene la actividad reciente del sistema"""
    actividades = []
    
    # Últimos cálculos
    calculos = CalculoHistorico.query.order_by(
        CalculoHistorico.fecha_calculo.desc()
    ).limit(limite // 2).all()
    
    for c in calculos:
        actividades.append({
            'tipo': 'calculo',
            'usuario': c.usuario.nombre_completo,
            'descripcion': f'Realizó {c.resumen}',
            'fecha': c.fecha_calculo
        })
    
    # Últimos portafolios
    portafolios = Portafolio.query.order_by(
        Portafolio.fecha_subida.desc()
    ).limit(limite // 2).all()
    
    for p in portafolios:
        actividades.append({
            'tipo': 'portafolio',
            'usuario': p.usuario.nombre_completo,
            'descripcion': f'Subió "{p.titulo}"',
            'fecha': p.fecha_subida
        })
    
    # Ordenar por fecha
    actividades.sort(key=lambda x: x['fecha'], reverse=True)
    return actividades[:limite]


def buscar_calculos_usuario(usuario_id, tipo=None, fecha_inicio=None, fecha_fin=None):
    """Busca cálculos de un usuario con filtros"""
    query = CalculoHistorico.query.filter_by(usuario_id=usuario_id)
    
    if tipo:
        query = query.filter_by(tipo_calculo=tipo)
    
    if fecha_inicio:
        query = query.filter(CalculoHistorico.fecha_calculo >= fecha_inicio)
    
    if fecha_fin:
        query = query.filter(CalculoHistorico.fecha_calculo <= fecha_fin)
    
    return query.order_by(CalculoHistorico.fecha_calculo.desc()).all()