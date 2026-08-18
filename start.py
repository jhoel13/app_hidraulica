# start.py - Script simplificado para iniciar la aplicación
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ============================================
# CONFIGURACIÓN
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-unc-2026'

# ¡¡¡IMPORTANTE!!! Cambia "tu_contraseña" por tu contraseña real de MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tu_contraseña@localhost/proyecto_hidraulica'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ============================================
# INICIALIZAR EXTENSIONES
# ============================================

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================
# MODELOS SIMPLIFICADOS
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

# ============================================
# RUTAS DE LA APLICACIÓN
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Usuario.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Credenciales incorrectas', 'error')
        return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            hashed_password = generate_password_hash(request.form.get('password'))
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
            flash('Registro exitoso', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
        
        Q = area * velocidad
        resultado = {
            'Caudal (m³/s)': round(Q, 4),
            'Caudal (L/s)': round(Q * 1000, 1),
            'Área (m²)': round(area, 4),
            'Velocidad (m/s)': round(velocidad, 2)
        }
        
        # Guardar en historial
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
        import math
        data = request.json
        Q = float(data.get('caudal', 0))
        D = float(data.get('diametro', 0))
        L = float(data.get('longitud', 0))
        rug = float(data.get('rugosidad', 0.00015))
        
        if Q <= 0 or D <= 0 or L <= 0:
            return jsonify({'error': 'Todos los valores deben ser mayores a 0'}), 400
        
        A = math.pi * (D ** 2) / 4
        V = Q / A
        nu = 1e-6
        Re = (V * D) / nu
        rugRel = rug / D
        
        # Colebrook-White simplificado
        f = 0.02
        for _ in range(10):
            f = 1 / math.pow(-2 * math.log10((rugRel / 3.7) + (2.51 / (Re * math.sqrt(f)))), 2)
        
        hf = f * (L / D) * (V ** 2) / (2 * 9.81)
        hm = 0.1 * hf
        
        resultado = {
            'Velocidad (m/s)': round(V, 2),
            'Reynolds': round(Re),
            'Factor de fricción': round(f, 4),
            'Pérdida fricción (m)': round(hf, 3),
            'Pérdida menor (m)': round(hm, 3),
            'Pérdida total (m)': round(hf + hm, 3)
        }
        
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
        import math
        data = request.json
        Q = float(data.get('caudal', 0)) / 1000
        L = float(data.get('longitud', 0))
        D_input = float(data.get('diametro', 0)) / 1000
        material = data.get('material', 'pvc')
        
        if Q <= 0 or L <= 0:
            return jsonify({'error': 'Caudal y longitud deben ser mayores a 0'}), 400
        
        V_recomendada = 1.5
        diametros = [25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 200, 250]
        
        if D_input == 0:
            A_requerida = Q / V_recomendada
            D_calc = math.sqrt(4 * A_requerida / math.pi)
            D_mm = D_calc * 1000
            D_seleccionado = min(diametros, key=lambda x: abs(x - D_mm))
            D = D_seleccionado / 1000
        else:
            D = D_input
            D_seleccionado = int(D * 1000)
        
        A = math.pi * (D ** 2) / 4
        V = Q / A
        
        resultado = {
            'Caudal (L/s)': round(Q * 1000, 1),
            'Diámetro (mm)': D_seleccionado,
            'Velocidad (m/s)': round(V, 2),
            'Material': material.upper(),
            'Recomendación': '✅ Velocidad adecuada' if 0.5 <= V <= 3 else '⚠️ Revisar velocidad'
        }
        
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
            os.makedirs('uploads', exist_ok=True)
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

# ============================================
# INICIALIZAR BASE DE DATOS
# ============================================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin
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
            print("✅ Usuario admin creado")
        
        # Crear usuario demo
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
            print("✅ Usuario demo creado")

# ============================================
# EJECUTAR APLICACIÓN
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("  🏗️  PLATAFORMA DE INGENIERÍA HIDRÁULICA - UNC")
    print("=" * 60)
    
    # Inicializar base de datos
    init_db()
    
    print("\n📋 CREDENCIALES DE PRUEBA:")
    print("  📧 admin@unc.edu.pe  🔑 admin123")
    print("  📧 demo@unc.edu.pe   🔑 demo123")
    print("\n🌐 Abre tu navegador en: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)