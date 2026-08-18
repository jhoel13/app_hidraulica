// ====== Funciones Principales ======

// Manejador de formularios
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    initTooltips();
    
    // Inicializar animaciones
    initAnimations();
    
    // Configurar eventos
    setupEventListeners();
});

function initTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    elements.forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.position = 'absolute';
            tooltip.style.background = '#0a1628';
            tooltip.style.color = 'white';
            tooltip.style.padding = '0.5rem 1rem';
            tooltip.style.borderRadius = '6px';
            tooltip.style.fontSize = '0.85rem';
            tooltip.style.zIndex = '1000';
            tooltip.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.bottom + 8) + 'px';
            
            document.body.appendChild(tooltip);
            
            this.addEventListener('mouseleave', function() {
                tooltip.remove();
            });
        });
    });
}

function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeUp');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.card, .stat-card, .form-container').forEach(el => {
        observer.observe(el);
    });
}

function setupEventListeners() {
    // Navegación móvil
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            document.querySelector('.nav-links').classList.toggle('active');
        });
    }
    
    // Manejar envío de formularios con AJAX
    document.querySelectorAll('form[data-ajax]').forEach(form => {
        form.addEventListener('submit', handleAjaxSubmit);
    });
    
    // Manejar botones de descarga
    document.querySelectorAll('.btn-download').forEach(btn => {
        btn.addEventListener('click', handleDownload);
    });
}

// ====== Funciones para el Asistente IA ======

function enviarConsultaIA() {
    const input = document.getElementById('iaInput');
    const mensaje = input.value.trim();
    
    if (!mensaje) return;
    
    // Agregar mensaje del usuario
    agregarMensaje(mensaje, 'user');
    input.value = '';
    
    // Mostrar indicador de escritura
    const loading = document.createElement('div');
    loading.className = 'message assistant';
    loading.innerHTML = '✍️ Pensando...';
    document.getElementById('chatMessages').appendChild(loading);
    
    // Enviar a la API
    fetch('/api/ia/consultar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ consulta: mensaje })
    })
    .then(response => response.json())
    .then(data => {
        loading.remove();
        if (data.error) {
            agregarMensaje('❌ Error: ' + data.error, 'assistant');
        } else {
            agregarMensaje(data.respuesta, 'assistant');
        }
        // Desplazar hacia abajo
        const container = document.getElementById('chatMessages');
        container.scrollTop = container.scrollHeight;
    })
    .catch(error => {
        loading.remove();
        agregarMensaje('❌ Error de conexión', 'assistant');
        console.error('Error:', error);
    });
}

function agregarMensaje(texto, tipo) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${tipo}`;
    div.innerHTML = texto;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ====== Funciones para Cálculos ======

function calcularCaudal() {
    const area = parseFloat(document.getElementById('area').value);
    const velocidad = parseFloat(document.getElementById('velocidad').value);
    
    if (!area || !velocidad) {
        mostrarError('Por favor ingresa todos los valores');
        return;
    }
    
    const data = { area, velocidad };
    
    fetch('/api/calcular/caudal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(resultado => {
        mostrarResultado('caudal', resultado);
        agregarHistorial('Cálculo de Caudal', data, resultado);
    })
    .catch(error => {
        mostrarError('Error al calcular: ' + error);
    });
}

function disenarCanal() {
    const caudal = parseFloat(document.getElementById('caudalCanal').value);
    const pendiente = parseFloat(document.getElementById('pendienteCanal').value);
    const rugosidad = parseFloat(document.getElementById('rugosidadCanal').value);
    const tipo = document.getElementById('tipoCanal').value;
    
    const data = { caudal, pendiente, rugosidad, tipo };
    
    fetch('/api/calcular/canal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(resultado => {
        mostrarResultado('canal', resultado);
    })
    .catch(error => {
        mostrarError('Error al diseñar canal: ' + error);
    });
}

function disenarTuberia() {
    const caudal = parseFloat(document.getElementById('caudalTuberia').value);
    const longitud = parseFloat(document.getElementById('longitudTuberia').value);
    const diametro = parseFloat(document.getElementById('diametroTuberia').value) || 0;
    const material = document.getElementById('materialTuberia').value;
    
    const data = { caudal, longitud, diametro, material };
    
    fetch('/api/calcular/tuberia', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(resultado => {
        mostrarResultado('tuberia', resultado);
    })
    .catch(error => {
        mostrarError('Error al diseñar tubería: ' + error);
    });
}

function calcularPerdidas() {
    const caudal = parseFloat(document.getElementById('caudalPerdidas').value);
    const diametro = parseFloat(document.getElementById('diametroPerdidas').value);
    const longitud = parseFloat(document.getElementById('longitudPerdidas').value);
    const rugosidad = parseFloat(document.getElementById('rugosidadPerdidas').value) || 0.00015;
    
    const data = { caudal, diametro, longitud, rugosidad };
    
    fetch('/api/calcular/perdidas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(resultado => {
        mostrarResultado('perdidas', resultado);
    })
    .catch(error => {
        mostrarError('Error al calcular pérdidas: ' + error);
    });
}

// ====== Funciones de Utilidad ======

function mostrarResultado(tipo, datos) {
    const container = document.getElementById('resultados');
    let html = '<div class="result-card animate-fadeUp"><h4>📊 Resultados</h4><ul>';
    
    for (const [key, value] of Object.entries(datos)) {
        if (typeof value === 'object' && value !== null) {
            html += `<li><strong>${key}:</strong> <pre>${JSON.stringify(value, null, 2)}</pre></li>`;
        } else {
            html += `<li><strong>${key}:</strong> ${value}</li>`;
        }
    }
    
    html += '</ul></div>';
    container.innerHTML = html;
}

function mostrarError(mensaje) {
    const container = document.getElementById('resultados');
    container.innerHTML = `<div class="error-message">❌ ${mensaje}</div>`;
}

function agregarHistorial(tipo, entrada, resultado) {
    // Guardar en localStorage para visualización offline
    const historial = JSON.parse(localStorage.getItem('historial_calculos') || '[]');
    historial.push({
        tipo,
        fecha: new Date().toISOString(),
        entrada,
        resultado
    });
    localStorage.setItem('historial_calculos', JSON.stringify(historial));
}

// ====== Funciones para Portafolio ======

function subirPortafolio() {
    const form = document.getElementById('portafolioForm');
    const formData = new FormData(form);
    
    fetch('/api/portafolio/subir', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error al subir: ' + error);
    });
}

// ====== Funciones para Exportar PDF ======

function exportarPDF(datos) {
    fetch('/api/generar_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'informe_hidraulico.pdf';
        a.click();
    })
    .catch(error => {
        console.error('Error al generar PDF:', error);
        alert('Error al generar el PDF');
    });
}

// ====== Funciones para el Mapa ======

let mapa = null;
let marcadores = [];

function inicializarMapa(elementId, center = [-6.5, -78.5], zoom = 9) {
    if (mapa) {
        mapa.invalidateSize();
        return mapa;
    }
    
    mapa = L.map(elementId).setView(center, zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapa);
    
    return mapa;
}

function agregarMarcador(lat, lng, popupTexto, icono = null) {
    const marker = L.marker([lat, lng]).addTo(mapa);
    
    if (popupTexto) {
        marker.bindPopup(popupTexto);
    }
    
    if (icono) {
        marker.setIcon(icono);
    }
    
    marcadores.push(marker);
    return marker;
}

function agregarPoligono(coordenadas, color = '#3388ff', popupTexto = '') {
    const polygon = L.polygon(coordenadas, {
        color: color,
        weight: 2,
        opacity: 0.7,
        fillOpacity: 0.3
    }).addTo(mapa);
    
    if (popupTexto) {
        polygon.bindPopup(popupTexto);
    }
    
    return polygon;
}

function limpiarMapa() {
    marcadores.forEach(marker => mapa.removeLayer(marker));
    marcadores = [];
}

// ====== Funciones para Simulación de Datos ======

function simularDatosRio() {
    const estaciones = [
        { nombre: 'Estación 1', caudal: 45 + Math.random() * 20, nivel: 2.5 + Math.random() * 0.8, temperatura: 18 + Math.random() * 4 },
        { nombre: 'Estación 2', caudal: 55 + Math.random() * 25, nivel: 3.0 + Math.random() * 1.0, temperatura: 20 + Math.random() * 3 },
        { nombre: 'Estación 3', caudal: 35 + Math.random() * 15, nivel: 1.8 + Math.random() * 0.5, temperatura: 19 + Math.random() * 2 }
    ];
    
    return estaciones;
}

function actualizarDatosRios() {
    const datos = simularDatosRio();
    const container = document.getElementById('datosRios');
    
    let html = '<div class="card-grid">';
    datos.forEach(estacion => {
        html += `
            <div class="card">
                <h4>${estacion.nombre}</h4>
                <p>💧 Caudal: ${estacion.caudal.toFixed(1)} m³/s</p>
                <p>📏 Nivel: ${estacion.nivel.toFixed(2)} m</p>
                <p>🌡️ Temperatura: ${estacion.temperatura.toFixed(1)} °C</p>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// ====== Función de ayuda para teclas ======

function handleKeyPress(event, callback) {
    if (event.key === 'Enter') {
        callback();
    }
}

// Exponer funciones globalmente
window.calcularCaudal = calcularCaudal;
window.disenarCanal = disenarCanal;
window.disenarTuberia = disenarTuberia;
window.calcularPerdidas = calcularPerdidas;
window.enviarConsultaIA = enviarConsultaIA;
window.subirPortafolio = subirPortafolio;
window.exportarPDF = exportarPDF;
window.actualizarDatosRios = actualizarDatosRios;
window.inicializarMapa = inicializarMapa;