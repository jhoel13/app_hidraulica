from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from models import db, Usuario, Portafolio, CalculoHistorico, Proyecto
from utils.hidraulica import (
    calcular_caudal, disenar_canal, calcular_perdidas_carga,
    calcular_reynolds, factor_friccion, disenar_tuberia,
    metodo_racional, hidrograma_unitario
)
from utils.ia_helper import IAHelper
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Crear directorios necesarios
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ============ RUTAS PRINCIPALES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Usuario.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            hashed_password = generate_password_hash(request.form['password'])
            usuario = Usuario(
                email=request.form['email'],
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                codigo_estudiante=request.form['codigo'],
                carrera=request.form['carrera'],
                password_hash=hashed_password
            )
            db.session.add(usuario)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('register.html', error=f'Error: {str(e)}')
    
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

# ============ CALCULADORAS HIDRÁULICAS ============

@app.route('/calculadora')
@login_required
def calculadora():
    return render_template('calculadora.html')

@app.route('/api/calcular/caudal', methods=['POST'])
@login_required
def api_calcular_caudal():
    data = request.json
    try:
        area = float(data['area'])
        velocidad = float(data['velocidad'])
        resultado = calcular_caudal(area, velocidad)
        
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
        return jsonify({'error': str(e)}), 400

@app.route('/api/calcular/canal', methods=['POST'])
@login_required
def api_calcular_canal():
    data = request.json
    try:
        caudal = float(data['caudal'])
        pendiente = float(data['pendiente'])
        rugosidad = float(data['rugosidad'])
        tipo = data.get('tipo', 'trapezoidal')
        
        resultado = disenar_canal(caudal, pendiente, rugosidad, tipo)
        
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
        return jsonify({'error': str(e)}), 400

@app.route('/api/calcular/tuberia', methods=['POST'])
@login_required
def api_calcular_tuberia():
    data = request.json
    try:
        caudal = float(data['caudal'])
        longitud = float(data['longitud'])
        diametro = float(data.get('diametro', 0))
        material = data.get('material', 'pvc')
        tipo = data.get('tipo', 'completo')
        
        resultado = disenar_tuberia(caudal, longitud, diametro, material, tipo)
        
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
        return jsonify({'error': str(e)}), 400

@app.route('/api/calcular/reynolds', methods=['POST'])
@login_required
def api_calcular_reynolds():
    data = request.json
    try:
        velocidad = float(data['velocidad'])
        diametro = float(data['diametro'])
        viscosidad = float(data.get('viscosidad', 0.000001))
        
        resultado = calcular_reynolds(velocidad, diametro, viscosidad)
        
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
        return jsonify({'error': str(e)}), 400

@app.route('/api/calcular/perdidas', methods=['POST'])
@login_required
def api_calcular_perdidas():
    data = request.json
    try:
        caudal = float(data['caudal'])
        diametro = float(data['diametro'])
        longitud = float(data['longitud'])
        rugosidad = float(data.get('rugosidad', 0.00015))
        
        resultado = calcular_perdidas_carga(caudal, diametro, longitud, rugosidad)
        
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
        return jsonify({'error': str(e)}), 400

# ============ IA ASISTENTE ============

@app.route('/ia_asistente')
@login_required
def ia_asistente():
    return render_template('ia_asistente.html')

@app.route('/api/ia/consultar', methods=['POST'])
@login_required
def api_ia_consultar():
    data = request.json
    consulta = data.get('consulta', '')
    
    try:
        ia = IAHelper()
        respuesta = ia.procesar_consulta(consulta)
        
        # Guardar en historial
        historial = CalculoHistorico(
            usuario_id=current_user.id,
            tipo_calculo='ia_consulta',
            datos_entrada={'consulta': consulta},
            resultados={'respuesta': respuesta}
        )
        db.session.add(historial)
        db.session.commit()
        
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/ia/diseñar', methods=['POST'])
@login_required
def api_ia_disenar():
    data = request.json
    try:
        ia = IAHelper()
        diseno = ia.disenar_proyecto(data)
        
        return jsonify(diseno)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ============ PORTAFOLIO ============

@app.route('/portafolio')
@login_required
def portafolio():
    portafolios = Portafolio.query.filter_by(usuario_id=current_user.id).all()
    return render_template('portafolio.html', portafolios=portafolios)

@app.route('/api/portafolio/subir', methods=['POST'])
@login_required
def api_subir_portafolio():
    try:
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        archivo = request.files['archivo']
        
        if archivo:
            filename = secure_filename(archivo.filename)
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
            
            return jsonify({'success': True, 'message': 'Portafolio subido exitosamente'})
        
        return jsonify({'error': 'No se subió ningún archivo'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/portafolio/eliminar/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_portafolio(id):
    portafolio = Portafolio.query.get_or_404(id)
    if portafolio.usuario_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    db.session.delete(portafolio)
    db.session.commit()
    return jsonify({'success': True})

# ============ OTRAS FUNCIONALIDADES ============

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

@app.route('/api/generar_pdf', methods=['POST'])
@login_required
def generar_pdf():
    data = request.json
    try:
        # Crear PDF con reportlab
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Título
        styles = getSampleStyleSheet()
        title = Paragraph("Informe de Cálculo Hidráulico", styles['Title'])
        story.append(title)
        
        # Datos del usuario
        story.append(Paragraph(f"Usuario: {current_user.nombre} {current_user.apellido}", styles['Normal']))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))
        
        # Resultados
        if 'resultados' in data:
            for key, value in data['resultados'].items():
                story.append(Paragraph(f"{key}: {value}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(buffer, download_name='informe_hidraulico.pdf', as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)