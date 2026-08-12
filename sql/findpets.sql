-- =========================================================
-- FINDPETS
-- BASE DE DATOS
-- =========================================================

CREATE DATABASE IF NOT EXISTS findpets;
USE findpets;

-- =========================================================
-- TABLA USUARIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    apellido VARCHAR(120) NOT NULL,
    correo VARCHAR(180) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    comuna VARCHAR(120),
    contrasena VARCHAR(255) NOT NULL,
    foto_perfil VARCHAR(255),
    rol VARCHAR(30) NOT NULL DEFAULT 'Usuario',
    estado VARCHAR(30) NOT NULL DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- TABLA MASCOTAS
-- =========================================================

CREATE TABLE IF NOT EXISTS mascotas (
    id_mascota INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    nombre VARCHAR(120),
    especie VARCHAR(50),
    raza VARCHAR(120),
    sexo VARCHAR(30),
    edad VARCHAR(30),
    color VARCHAR(80),
    estado VARCHAR(30) NOT NULL DEFAULT 'Perdida',
    ubicacion VARCHAR(180),
    fecha DATE,
    descripcion TEXT,
    foto VARCHAR(255),
    codigo VARCHAR(30) NOT NULL UNIQUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mascota_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- TABLA COMENTARIOS
-- (id_publicacion hace referencia a mascotas(id_mascota):
--  el muro usa las mascotas como publicaciones)
-- =========================================================

CREATE TABLE IF NOT EXISTS comentarios (
    id_comentario INT AUTO_INCREMENT PRIMARY KEY,
    id_publicacion INT NOT NULL,
    id_usuario INT NOT NULL,
    comentario VARCHAR(600) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comentario_mascota
        FOREIGN KEY (id_publicacion)
        REFERENCES mascotas(id_mascota)
        ON DELETE CASCADE,
    CONSTRAINT fk_comentario_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- TABLA REACCIONES
-- =========================================================

CREATE TABLE IF NOT EXISTS reacciones (
    id_reaccion INT AUTO_INCREMENT PRIMARY KEY,
    id_publicacion INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_publicacion, id_usuario),
    CONSTRAINT fk_reaccion_mascota
        FOREIGN KEY (id_publicacion)
        REFERENCES mascotas(id_mascota)
        ON DELETE CASCADE,
    CONSTRAINT fk_reaccion_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- TABLA CONVERSACIONES
-- =========================================================

CREATE TABLE IF NOT EXISTS conversaciones (
    id_chat INT AUTO_INCREMENT PRIMARY KEY,
    id_mascota INT,
    usuario_1 INT NOT NULL,
    usuario_2 INT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'Activa',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    CONSTRAINT fk_chat_mascota
        FOREIGN KEY (id_mascota)
        REFERENCES mascotas(id_mascota)
        ON DELETE SET NULL,
    CONSTRAINT fk_chat_usuario1
        FOREIGN KEY (usuario_1)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE,
    CONSTRAINT fk_chat_usuario2
        FOREIGN KEY (usuario_2)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- TABLA MENSAJES
-- =========================================================

CREATE TABLE IF NOT EXISTS mensajes (
    id_mensaje INT AUTO_INCREMENT PRIMARY KEY,
    id_chat INT NOT NULL,
    id_usuario INT NOT NULL,
    mensaje TEXT,
    imagen VARCHAR(255),
    ubicacion VARCHAR(255),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mensaje_chat
        FOREIGN KEY (id_chat)
        REFERENCES conversaciones(id_chat)
        ON DELETE CASCADE,
    CONSTRAINT fk_mensaje_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;