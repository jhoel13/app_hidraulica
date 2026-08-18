# app_sqlite.py - Versión con SQLite (NO necesita MySQL)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import math

# ============================================
# CONFIGURACIÓN
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-unc-2026'

# USANDO SQLITE - No necesita MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hidraulica.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de archivos
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Crear carpetas necesarias
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# ============================================
# INICIALIZAR EXTENSIONES
# ============================================

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder'

# ============================================
# MODELOS DE BASE DE DATOS
# ============================================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    codigo_estudiante = db.Column(db.String(20), unique=True)
    carrera = db.Column(db.String(50))
    password_hash = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    es_activo = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='estudiante')

class Portafolio(db.Model):
    __tablename__ = 'portafolios'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    archivo_path = db.Column(db.String(500))
    tipo_archivo = db.Column(db.String(50))
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    es_publico = db.Column(db.Boolean, default=True)

class CalculoHistorico(db.Model):
    __tablename__ = 'calculos_historicos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo_calculo = db.Column(db.String(50), nullable=False)
    datos_entrada = db.Column(db.JSON)
    resultados = db.Column(db.JSON)
    fecha_calculo = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def calcular_caudal(area, velocidad):
    Q = area * velocidad
    return {
        'caudal_m3s': round(Q, 4),
        'caudal_lps': round(Q * 1000, 1),
        'area': round(area, 4),
        'velocidad': round(velocidad, 2)
    }

def calcular_perdidas(Q, D, L, rugosidad):
    A = math.pi * (D ** 2) / 4
    V = Q / A
    nu = 1e-6
    Re = (V * D) / nu
    rugRel = rugosidad / D
    
    # Colebrook-White
    f = 0.02
    for _ in range(10):
        try:
            f = 1 / math.pow(-2 * math.log10((rugRel / 3.7) + (2.51 / (Re * math.sqrt(f)))), 2)
        except:
            f = 0.02
            break
    
    hf = f * (L / D) * (V ** 2) / (2 * 9.81)
    hm = 0.1 * hf
    
    return {
        'velocidad': round(V, 2),
        'reynolds': round(Re),
        'factor_friccion': round(f, 4),
        'perdida_friccion': round(hf, 3),
        'perdida_menor': round(hm, 3),
        'perdida_total': round(hf + hm, 3)
    }

def disenar_tuberia(Q, L, D_input, material):
    V_recomendada = 1.5
    diametros = [25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 200, 250]
    
    if D_input == 0:
        A_requerida = Q / V_recomendada
        D_calc = math.sqrt(4 * A_requerida / math.pi)
        D_mm = D_calc * 1000
        D_seleccionado = min(diametros, key=lambda x: abs(x - D_mm))
        D = D_seleccionado / 1000
    else:
        D = D_input / 1000
        D_seleccionado = int(D * 1000)
    
    A = math.pi * (D ** 2) / 4
    V = Q / A
    
    return {
        'caudal_lps': round(Q * 1000, 1),
        'diametro_mm': D_seleccionado,
        'velocidad': round(V, 2),
        'material': material.upper(),
        'recomendacion': '✅ Adecuada' if 0.5 <= V <= 3 else '⚠️ Revisar'
    }

# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            password = request.form.get('password')
            password2 = request.form.get('password2')
            
            if password != password2:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('register.html')
            
            if Usuario.query.filter_by(email=request.form.get('email')).first():
                flash('Este email ya está registrado', 'error')
                return render_template('register.html')
            
            hashed_password = generate_password_hash(password)
            usuario = Usuario(
                email=request.form.get('email'),
                nombre=request.form.get('nombre'),
                apellido=request.form.get('apellido'),
                codigo_estudiante=request.form.get('codigo'),
                carrera=request.form.get('carrera'),
                password_hash=hashed_password
            )
            db.session.add(usuario)
            db.session.commit()
            flash('Registro exitoso. ¡Bienvenido!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    portafolios = Portafolio.query.filter_by(usuario_id=current_user.id).all()
    calculos = CalculoHistorico.query.filter_by(usuario_id=current_user.id).order_by(
        CalculoHistorico.fecha_calculo.desc()
    ).limit(10).all()
    return render_template('dashboard.html', portafolios=portafolios, calculos=calculos)

# ============================================
# RUTAS DE CÁLCULO
# ============================================

@app.route('/calculadora')
@login_required
def calculadora():
    return render_template('calculadora.html')

@app.route('/api/calcular/caudal', methods=['POST'])
@login_required
def api_calcular_caudal():
    try:
        data = request.json
        area = float(data.get('area', 0))
        velocidad = float(data.get('velocidad', 0))
        
        if area <= 0 or velocidad <= 0:
            return jsonify({'error': 'Valores deben ser mayores a 0'}), 400
        
        resultado = calcular_caudal(area, velocidad)
        
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='caudal',
            datos_entrada=data,
            resultados=resultado
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calcular/perdidas', methods=['POST'])
@login_required
def api_calcular_perdidas():
    try:
        data = request.json
        Q = float(data.get('caudal', 0))
        D = float(data.get('diametro', 0))
        L = float(data.get('longitud', 0))
        rug = float(data.get('rugosidad', 0.00015))
        
        if Q <= 0 or D <= 0 or L <= 0:
            return jsonify({'error': 'Todos los valores deben ser mayores a 0'}), 400
        
        resultado = calcular_perdidas(Q, D, L, rug)
        
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='perdidas',
            datos_entrada=data,
            resultados=resultado
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calcular/tuberia', methods=['POST'])
@login_required
def api_calcular_tuberia():
    try:
        data = request.json
        Q = float(data.get('caudal', 0)) / 1000
        L = float(data.get('longitud', 0))
        D_input = float(data.get('diametro', 0))
        material = data.get('material', 'pvc')
        
        if Q <= 0 or L <= 0:
            return jsonify({'error': 'Caudal y longitud deben ser mayores a 0'}), 400
        
        resultado = disenar_tuberia(Q, L, D_input, material)
        
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='tuberia',
            datos_entrada=data,
            resultados=resultado
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calcular/reynolds', methods=['POST'])
@login_required
def api_calcular_reynolds():
    try:
        data = request.json
        velocidad = float(data.get('velocidad', 0))
        diametro = float(data.get('diametro', 0))
        viscosidad = float(data.get('viscosidad', 0.000001))
        
        if velocidad <= 0 or diametro <= 0:
            return jsonify({'error': 'Valores deben ser mayores a 0'}), 400
        
        Re = (velocidad * diametro) / viscosidad
        tipo = 'Turbulento' if Re > 4000 else 'Laminar' if Re < 2000 else 'Transición'
        
        resultado = {
            'reynolds': round(Re),
            'tipo': tipo,
            'velocidad': round(velocidad, 2),
            'diametro': round(diametro, 4)
        }
        
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='reynolds',
            datos_entrada=data,
            resultados=resultado
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calcular/canal', methods=['POST'])
@login_required
def api_calcular_canal():
    try:
        data = request.json
        Q = float(data.get('caudal', 0))
        S = float(data.get('pendiente', 0))
        n = float(data.get('rugosidad', 0))
        tipo = data.get('tipo', 'trapezoidal')
        
        if Q <= 0 or S <= 0 or n <= 0:
            return jsonify({'error': 'Todos los valores deben ser mayores a 0'}), 400
        
        y = math.pow((Q * n / math.sqrt(S)), 0.6)
        resultado = {'tipo': tipo}
        
        if tipo == 'trapezoidal':
            z = 1
            b = 2 * y * (math.sqrt(1 + z**2) - z)
            A = (b + z * y) * y
            P = b + 2 * y * math.sqrt(1 + z**2)
            R = A / P
            resultado.update({
                'base': round(b, 3),
                'tirante': round(y, 3),
                'area': round(A, 3),
                'perimetro': round(P, 3),
                'radio_hidraulico': round(R, 3)
            })
        elif tipo == 'rectangular':
            b = Q / (y * math.sqrt(S) / n)
            A = b * y
            P = b + 2 * y
            R = A / P
            resultado.update({
                'base': round(b, 3),
                'tirante': round(y, 3),
                'area': round(A, 3),
                'perimetro': round(P, 3),
                'radio_hidraulico': round(R, 3)
            })
        elif tipo == 'circular':
            D = math.pow((Q * n / math.sqrt(S)), 0.6)
            yc = 0.8 * D
            theta = 2 * math.acos(1 - 2 * yc / D)
            A = (D ** 2 / 8) * (theta - math.sin(theta))
            P = D * theta / 2
            R = A / P
            resultado.update({
                'diametro': round(D, 3),
                'tirante': round(yc, 3),
                'area': round(A, 3),
                'perimetro': round(P, 3),
                'radio_hidraulico': round(R, 3)
            })
        
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='canal',
            datos_entrada=data,
            resultados=resultado
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# OTRAS RUTAS
# ============================================

@app.route('/canales')
@login_required
def canales():
    return render_template('canales.html')

@app.route('/tuberias')
@login_required
def tuberias():
    return render_template('tuberias.html')

@app.route('/rios')
@login_required
def rios():
    return render_template('rios.html')

@app.route('/red_agua')
@login_required
def red_agua():
    return render_template('red_agua.html')

@app.route('/ia_asistente')
@login_required
def ia_asistente():
    return render_template('ia_asistente.html')

@app.route('/inundaciones')
@login_required
def inundaciones():
    return render_template('inundaciones.html')

@app.route('/presas')
@login_required
def presas():
    return render_template('presas.html')

@app.route('/biblioteca')
@login_required
def biblioteca():
    return render_template('biblioteca.html')

@app.route('/hidrologia')
@login_required
def hidrologia():
    return render_template('hidrologia.html')

@app.route('/portafolio')
@login_required
def portafolio():
    portafolios = Portafolio.query.filter_by(usuario_id=current_user.id).all()
    return render_template('portafolio.html', portafolios=portafolios)

@app.route('/api/portafolio/subir', methods=['POST'])
@login_required
def api_subir_portafolio():
    try:
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        archivo = request.files.get('archivo')
        
        if not titulo:
            return jsonify({'error': 'El título es obligatorio'}), 400
        
        if archivo:
            filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.filename}")
            filepath = os.path.join('uploads', filename)
            archivo.save(filepath)
            
            portafolio = Portafolio(
                usuario_id=current_user.id,
                titulo=titulo,
                descripcion=descripcion,
                archivo_path=filepath,
                tipo_archivo=archivo.content_type
            )
            db.session.add(portafolio)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Portafolio subido'})
        
        return jsonify({'error': 'No se subió archivo'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portafolio/eliminar/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_portafolio(id):
    try:
        portafolio = Portafolio.query.get_or_404(id)
        if portafolio.usuario_id != current_user.id:
            return jsonify({'error': 'No autorizado'}), 403
        
        if os.path.exists(portafolio.archivo_path):
            os.remove(portafolio.archivo_path)
        
        db.session.delete(portafolio)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# INICIALIZAR BASE DE DATOS
# ============================================

def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Base de datos SQLite creada")
        
        # Crear admin
        if not Usuario.query.filter_by(email='admin@unc.edu.pe').first():
            admin = Usuario(
                email='admin@unc.edu.pe',
                nombre='Administrador',
                apellido='UNC',
                codigo_estudiante='ADMIN001',
                carrera='Ingeniería Hidráulica',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin creado")
        
        # Crear demo
        if not Usuario.query.filter_by(email='demo@unc.edu.pe').first():
            demo = Usuario(
                email='demo@unc.edu.pe',
                nombre='Usuario',
                apellido='Demo',
                codigo_estudiante='DEMO001',
                carrera='Ingeniería Civil',
                password_hash=generate_password_hash('demo123'),
                role='estudiante'
            )
            db.session.add(demo)
            db.session.commit()
            print("✅ Demo creado")

# ============================================
# EJECUTAR
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("  🏗️  PLATAFORMA DE INGENIERÍA HIDRÁULICA - UNC")
    print("  📦 Usando SQLite (No necesita MySQL)")
    print("=" * 60)
    
    init_db()
    
    print("\n📋 CREDENCIALES DE PRUEBA:")
    print("  📧 admin@unc.edu.pe  🔑 admin123")
    print("  📧 demo@unc.edu.pe   🔑 demo123")
    print("\n🌐 Abre tu navegador en: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)