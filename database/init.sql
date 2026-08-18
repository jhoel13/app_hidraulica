CREATE DATABASE proyecto_hidraulica;
USE proyecto_hidraulica;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    codigo_estudiante VARCHAR(20) UNIQUE,
    carrera VARCHAR(50),
    password_hash VARCHAR(200) NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    es_activo BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'estudiante'
);

-- Tabla de portafolios
CREATE TABLE portafolios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    archivo_path VARCHAR(500),
    tipo_archivo VARCHAR(50),
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    es_publico BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de cálculos históricos
CREATE TABLE calculos_historicos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    tipo_calculo VARCHAR(50) NOT NULL,
    datos_entrada JSON,
    resultados JSON,
    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
    pdf_generado VARCHAR(500),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de proyectos
CREATE TABLE proyectos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(50),
    datos JSON,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_usuario_email ON usuarios(email);
CREATE INDEX idx_portafolio_usuario ON portafolios(usuario_id);
CREATE INDEX idx_calculos_usuario ON calculos_historicos(usuario_id);
CREATE INDEX idx_proyectos_usuario ON proyectos(usuario_id);