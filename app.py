import os
import uuid
from datetime import datetime, date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from mysqlconnection import connectToMySQL

app = Flask(__name__)

app.secret_key = "findpets"

CARPETA_UPLOADS = os.path.join(os.path.dirname(__file__), "static", "uploads")
app.config["UPLOAD_FOLDER"] = CARPETA_UPLOADS

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


# =========================================================
# FUNCIONES DE APOYO
# =========================================================

def conectar_bd():
    return connectToMySQL("findpets")


def nombre_archivo_unico(archivo):
    if not archivo or archivo.filename == "":
        return None

    if not archivo.filename.rsplit(".", 1)[-1].lower() in EXTENSIONES_PERMITIDAS:
        return None

    nombre = secure_filename(archivo.filename)
    extension = nombre.rsplit(".", 1)[-1].lower()
    nombre_final = uuid.uuid4().hex + "." + extension

    archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_final))

    return nombre_final


def tiempo_relativo(fecha):
    try:
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
        elif isinstance(fecha, date) and not isinstance(fecha, datetime):
            fecha = datetime.combine(fecha, datetime.min.time())
    except (ValueError, TypeError):
        return "recientemente"

    diferencia = datetime.now() - fecha

    if diferencia.days > 30:
        return "hace más de un mes"
    if diferencia.days >= 1:
        return f"hace {diferencia.days} días"
    horas = diferencia.seconds // 3600
    if horas >= 1:
        return f"hace {horas} horas"
    minutos = (diferencia.seconds // 60) % 60
    if minutos >= 1:
        return f"hace {minutos} minutos"
    return "hace un momento"


def requiere_sesion():
    if "usuario_id" not in session:
        flash("Debes iniciar sesión para continuar.", "error")
        return redirect(url_for("iniciosesion"))

    return None


def requiere_admin():
    if "usuario_id" not in session:
        flash("Debes iniciar sesión para continuar.", "error")
        return redirect(url_for("iniciosesion"))

    if session.get("rol") != "Administrador":
        flash("No tienes permisos para entrar aquí.", "error")
        return redirect(url_for("inicio"))

    return None


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def inicio():

    mysql = conectar_bd()

    mascotas_recientes = mysql.query_db(
        """
        SELECT id_mascota, nombre, especie, raza, estado,
            ubicacion, foto,
            DATE_FORMAT(fecha, '%%d/%%m/%%Y') AS fecha
        FROM mascotas
        ORDER BY fecha_registro DESC
        LIMIT 6
        """
    )

    if not mascotas_recientes:
        mascotas_recientes = []

    return render_template(
        "index.html",
        mascotas_recientes=mascotas_recientes
    )


# =========================================================
# REGISTRO DE USUARIOS
# =========================================================

@app.route("/registrate", methods=["GET", "POST"])
def registrate():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        comuna = request.form.get("comuna", "").strip()
        contrasena = request.form.get("contrasena", "")
        confirmar_contrasena = request.form.get("confirmar_contrasena", "")

        if not nombre or not apellido or not correo or not contrasena:
            flash("Completa todos los campos obligatorios.", "error")
            return render_template("registro.html")

        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("registro.html")

        if len(contrasena) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("registro.html")

        mysql = conectar_bd()

        existe = mysql.query_db(
            "SELECT id_usuario FROM usuarios WHERE correo = %s",
            (correo,)
        )

        if existe:
            flash("Ya existe una cuenta con ese correo.", "error")
            return render_template("registro.html")

        resultado = mysql.query_db(
            """
            INSERT INTO usuarios
                (nombre, apellido, correo, telefono, comuna, contrasena,
                rol, estado, foto_perfil)
            VALUES (%s, %s, %s, %s, %s, %s, 'Usuario', 'Activo', NULL)
            """,
            (
                nombre,
                apellido,
                correo,
                telefono,
                comuna,
                generate_password_hash(contrasena)
            )
        )

        if not resultado:
            flash("No se pudo crear la cuenta. Intenta nuevamente.", "error")
            return render_template("registro.html")

        flash("Cuenta creada correctamente. Inicia sesión.", "exito")
        return redirect(url_for("iniciosesion"))

    return render_template("registro.html")


# =========================================================
# INICIO DE SESIÓN
# =========================================================

@app.route("/iniciosesion", methods=["GET", "POST"])
def iniciosesion():

    if request.method == "POST":

        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        mysql = conectar_bd()

        usuario = mysql.query_db(
            "SELECT * FROM usuarios WHERE correo = %s",
            (correo,)
        )

        if not usuario:
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("inicio_sesion.html")

        usuario = usuario[0]

        if usuario["estado"] == "Bloqueado":
            flash("Tu cuenta está bloqueada. Contacta al administrador.", "error")
            return render_template("inicio_sesion.html")

        if not check_password_hash(usuario["contrasena"], contrasena):
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("inicio_sesion.html")

        session["usuario_id"] = usuario["id_usuario"]
        session["nombre"] = usuario["nombre"]
        session["correo"] = usuario["correo"]
        session["rol"] = usuario["rol"]
        session["foto_perfil"] = usuario["foto_perfil"]

        if usuario["rol"] == "Administrador":
            return redirect(url_for("paneladministrador"))

        return redirect(url_for("inicio"))

    return render_template("inicio_sesion.html")


@app.route("/cerrar-sesion")
def cerrar_sesion():

    session.clear()

    return redirect(url_for("inicio"))


# =========================================================
# MI CUENTA
# =========================================================

@app.route("/mi-cuenta")
def paneldelusuario():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    usuario = mysql.query_db(
        "SELECT * FROM usuarios WHERE id_usuario = %s",
        (session["usuario_id"],)
    )

    reportes = mysql.query_db(
        """
        SELECT id_mascota, nombre, estado, ubicacion, foto,
            DATE_FORMAT(fecha, '%%d/%%m/%%Y') AS fecha
        FROM mascotas
        WHERE id_usuario = %s
        ORDER BY fecha_registro DESC
        """,
        (session["usuario_id"],)
    )

    if not usuario:
        session.clear()
        return redirect(url_for("iniciosesion"))

    if not reportes:
        reportes = []

    return render_template(
        "paneldeusuario.html",
        usuario=usuario[0],
        reportes=reportes
    )


@app.route("/actualizar-perfil", methods=["POST"])
def actualizar_perfil():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()
    comuna = request.form.get("comuna", "").strip()
    foto_perfil = request.files.get("foto_perfil")

    if not nombre or not apellido or not correo:
        flash("Completa todos los campos obligatorios.", "error")
        return redirect(url_for("paneldelusuario"))

    mysql = conectar_bd()

    repetido = mysql.query_db(
        """
        SELECT id_usuario FROM usuarios
        WHERE correo = %s AND id_usuario != %s
        """,
        (correo, session["usuario_id"])
    )

    if repetido:
        flash("Ese correo ya está en uso por otra cuenta.", "error")
        return redirect(url_for("paneldelusuario"))

    if foto_perfil and foto_perfil.filename != "":
        nuevo_nombre = nombre_archivo_unico(foto_perfil)

        if nuevo_nombre:
            session["foto_perfil"] = nuevo_nombre
        else:
            flash("Formato de imagen no permitido.", "error")
            return redirect(url_for("paneldelusuario"))

    mysql.query_db(
        """
        UPDATE usuarios
        SET nombre = %s, apellido = %s, correo = %s,
            telefono = %s, comuna = %s, foto_perfil = %s
        WHERE id_usuario = %s
        """,
        (
            nombre,
            apellido,
            correo,
            telefono,
            comuna,
            session.get("foto_perfil"),
            session["usuario_id"]
        )
    )

    session["nombre"] = nombre
    session["correo"] = correo

    flash("Perfil actualizado correctamente.", "exito")
    return redirect(url_for("paneldelusuario"))


@app.route("/cambiar-contrasena", methods=["POST"])
def cambiar_contrasena():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    contrasena_actual = request.form.get("contrasena_actual", "")
    nueva_contrasena = request.form.get("nueva_contrasena", "")
    confirmar_contrasena = request.form.get("confirmar_contrasena", "")

    mysql = conectar_bd()

    usuario = mysql.query_db(
        "SELECT contrasena FROM usuarios WHERE id_usuario = %s",
        (session["usuario_id"],)
    )

    if not usuario:
        flash("No se encontró tu cuenta.", "error")
        return redirect(url_for("paneldelusuario"))

    if not check_password_hash(usuario[0]["contrasena"], contrasena_actual):
        flash("La contraseña actual es incorrecta.", "error")
        return redirect(url_for("paneldelusuario"))

    if nueva_contrasena != confirmar_contrasena:
        flash("Las nuevas contraseñas no coinciden.", "error")
        return redirect(url_for("paneldelusuario"))

    if len(nueva_contrasena) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "error")
        return redirect(url_for("paneldelusuario"))

    mysql.query_db(
        """
        UPDATE usuarios SET contrasena = %s
        WHERE id_usuario = %s
        """,
        (generate_password_hash(nueva_contrasena), session["usuario_id"])
    )

    flash("Contraseña cambiada correctamente.", "exito")
    return redirect(url_for("paneldelusuario"))


@app.route("/eliminar-cuenta", methods=["POST"])
def eliminar_cuenta():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mysql.query_db(
        "DELETE FROM usuarios WHERE id_usuario = %s",
        (session["usuario_id"],)
    )

    session.clear()

    flash("Tu cuenta fue eliminada.", "exito")
    return redirect(url_for("inicio"))


# =========================================================
# REGISTRAR MASCOTA
# =========================================================

def generar_codigo():

    import random
    import string

    mysql = conectar_bd()

    while True:

        codigo = "FP-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )

        existe = mysql.query_db(
            "SELECT id_mascota FROM mascotas WHERE codigo = %s",
            (codigo,)
        )

        if not existe:
            return codigo


@app.route("/formulariomascota", methods=["GET", "POST"])
def formulariomascota():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    if request.method == "POST":

        id_mascota = request.form.get("id_mascota")
        nombre = request.form.get("nombre", "").strip()
        especie = request.form.get("especie", "").strip()
        raza = request.form.get("raza", "").strip()
        sexo = request.form.get("sexo", "").strip()
        edad = request.form.get("edad", "").strip()
        color = request.form.get("color", "").strip()
        estado = request.form.get("estado", "").strip()
        ubicacion = request.form.get("ubicacion", "").strip()
        fecha = request.form.get("fecha", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        foto = request.files.get("foto")

        if not estado:
            estado = "Perdida"

        if not fecha:
            fecha = date.today().strftime("%Y-%m-%d")

        foto_guardada = None

        if foto and foto.filename != "":
            foto_guardada = nombre_archivo_unico(foto)

        mysql = conectar_bd()

        if id_mascota:
            pertenece = mysql.query_db(
                "SELECT id_mascota FROM mascotas WHERE id_mascota = %s AND id_usuario = %s",
                (id_mascota, session["usuario_id"])
            )

            if not pertenece:
                flash("No puedes editar esa mascota.", "error")
                return redirect(url_for("mis_mascotas"))

            if foto_guardada:
                mysql.query_db(
                    """
                    UPDATE mascotas
                    SET nombre = %s, especie = %s, raza = %s, sexo = %s,
                        edad = %s, color = %s, estado = %s, ubicacion = %s,
                        fecha = %s, descripcion = %s, foto = %s
                    WHERE id_mascota = %s
                    """,
                    (
                        nombre,
                        especie,
                        raza,
                        sexo,
                        edad,
                        color,
                        estado,
                        ubicacion,
                        fecha,
                        descripcion,
                        foto_guardada,
                        id_mascota
                    )
                )
            else:
                mysql.query_db(
                    """
                    UPDATE mascotas
                    SET nombre = %s, especie = %s, raza = %s, sexo = %s,
                        edad = %s, color = %s, estado = %s, ubicacion = %s,
                        fecha = %s, descripcion = %s
                    WHERE id_mascota = %s
                    """,
                    (
                        nombre,
                        especie,
                        raza,
                        sexo,
                        edad,
                        color,
                        estado,
                        ubicacion,
                        fecha,
                        descripcion,
                        id_mascota
                    )
                )

            flash("Mascota actualizada correctamente.", "exito")
            return redirect(url_for("mis_mascotas"))

        codigo = generar_codigo()

        mysql.query_db(
            """
            INSERT INTO mascotas
                (id_usuario, nombre, especie, raza, sexo, edad, color,
                estado, ubicacion, fecha, descripcion, foto, codigo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["usuario_id"],
                nombre,
                especie,
                raza,
                sexo,
                edad,
                color,
                estado,
                ubicacion,
                fecha,
                descripcion,
                foto_guardada,
                codigo
            )
        )

        flash("Mascota registrada con su código FindPets.", "exito")
        return redirect(url_for("mis_mascotas"))

    return render_template("formulariomascota.html", mascota=None, codigo=None)


@app.route("/mascota/<int:id_mascota>/editar")
def editar_mascota(id_mascota):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mascota = mysql.query_db(
        """
        SELECT * FROM mascotas
        WHERE id_mascota = %s AND id_usuario = %s
        """,
        (id_mascota, session["usuario_id"])
    )

    if not mascota:
        flash("No se encontró esa mascota.", "error")
        return redirect(url_for("mis_mascotas"))

    return render_template(
        "formulariomascota.html",
        mascota=mascota[0],
        codigo=mascota[0]["codigo"]
    )


# =========================================================
# MIS MASCOTAS
# =========================================================

@app.route("/mis-mascotas")
def mis_mascotas():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mascotas = mysql.query_db(
        """
        SELECT id_mascota, nombre, especie, raza, sexo, edad, color,
            estado, ubicacion, foto, codigo
        FROM mascotas
        WHERE id_usuario = %s
        ORDER BY fecha_registro DESC
        """,
        (session["usuario_id"],)
    )

    if not mascotas:
        mascotas = []

    return render_template("mis_mascotas.html", mascotas=mascotas)


@app.route("/mascota/<int:id_mascota>/estado", methods=["POST"])
def cambiar_estado_mascota(id_mascota):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mascota = mysql.query_db(
        "SELECT id_mascota, estado FROM mascotas WHERE id_mascota = %s AND id_usuario = %s",
        (id_mascota, session["usuario_id"])
    )

    if not mascota:
        flash("No puedes modificar esa mascota.", "error")
        return redirect(url_for("mis_mascotas"))

    nuevo_estado = (
        "Encontrada" if mascota[0]["estado"] == "Perdida" else "Perdida"
    )

    mysql.query_db(
        """
        UPDATE mascotas SET estado = %s
        WHERE id_mascota = %s AND id_usuario = %s
        """,
        (nuevo_estado, id_mascota, session["usuario_id"])
    )

    if nuevo_estado == "Encontrada":
        cerrar_conversaciones_mascota(mysql, id_mascota)

    flash("Estado actualizado correctamente.", "exito")
    return redirect(url_for("mis_mascotas"))


@app.route("/mascota/<int:id_mascota>/eliminar", methods=["POST"])
def eliminar_mascota(id_mascota):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mysql.query_db(
        """
        DELETE FROM mascotas
        WHERE id_mascota = %s AND id_usuario = %s
        """,
        (id_mascota, session["usuario_id"])
    )

    flash("Mascota eliminada.", "exito")
    return redirect(url_for("mis_mascotas"))


# =========================================================
# BUSCAR MASCOTA
# =========================================================

@app.route("/buscar-mascota")
def buscar_mascota():

    busqueda = request.args.get("busqueda", "").strip()
    especie = request.args.get("especie", "").strip()
    estado = request.args.get("estado", "").strip()
    sexo = request.args.get("sexo", "").strip()
    ubicacion = request.args.get("ubicacion", "").strip()

    condiciones = []
    parametros = []

    if busqueda:
        condiciones.append(
            "(nombre LIKE %s OR raza LIKE %s OR color LIKE %s OR ubicacion LIKE %s)"
        )
        parametros.extend([f"%{busqueda}%"] * 4)

    if especie:
        condiciones.append("especie = %s")
        parametros.append(especie)

    if estado:
        condiciones.append("estado = %s")
        parametros.append(estado)

    if sexo:
        condiciones.append("sexo = %s")
        parametros.append(sexo)

    if ubicacion:
        condiciones.append("ubicacion LIKE %s")
        parametros.append(f"%{ubicacion}%")

    where = " AND ".join(condiciones)

    if where:
        where = "WHERE " + where

    consulta = f"""
        SELECT id_mascota, nombre, especie, raza, color, estado,
            ubicacion, foto,
            DATE_FORMAT(fecha, '%%d/%%m/%%Y') AS fecha
        FROM mascotas
        {where}
        ORDER BY fecha_registro DESC
    """

    mysql = conectar_bd()

    mascotas = mysql.query_db(consulta, parametros)

    if not mascotas:
        mascotas = []

    return render_template("buscar_mascota.html", mascotas=mascotas)


# =========================================================
# BUSCAR POR CÓDIGO
# =========================================================

@app.route("/buscarporcodigo")
def buscarporcodigo():

    codigo = request.args.get("codigo", "").strip().upper()

    mascota = None
    error = None

    if codigo:

        mysql = conectar_bd()

        resultado = mysql.query_db(
            """
            SELECT m.id_mascota, m.codigo, m.nombre, m.especie, m.raza,
                m.sexo, m.edad, m.color, m.estado, m.ubicacion, m.foto,
                m.descripcion,
                DATE_FORMAT(m.fecha, '%%d/%%m/%%Y') AS fecha
            FROM mascotas m
            WHERE m.codigo = %s
            """,
            (codigo,)
        )

        if resultado:
            mascota = resultado[0]
        else:
            error = "No se encontró una mascota con ese código."

    return render_template(
        "buscarporcodigo.html",
        mascota=mascota,
        error=error
    )


@app.route("/mascota/<int:id_mascota>")
def detalle_mascota(id_mascota):

    mysql = conectar_bd()

    resultado = mysql.query_db(
        """
        SELECT m.id_mascota, m.codigo, m.nombre, m.especie, m.raza,
            m.sexo, m.edad, m.color, m.estado, m.ubicacion, m.foto,
            m.descripcion,
            DATE_FORMAT(m.fecha, '%%d/%%m/%%Y') AS fecha
        FROM mascotas m
        WHERE m.id_mascota = %s
        """,
        (id_mascota,)
    )

    if not resultado:
        return redirect(url_for("buscar_mascota"))

    return render_template(
        "buscarporcodigo.html",
        mascota=resultado[0],
        error=None
    )


# =========================================================
# MURO COMUNITARIO
# =========================================================

@app.route("/murocomunitario")
def murocomunitario():

    busqueda = request.args.get("busqueda", "").strip()
    estado = request.args.get("estado", "").strip()
    especie = request.args.get("especie", "").strip()

    condiciones = []
    parametros = []

    if busqueda:
        condiciones.append(
            "(m.nombre LIKE %s OR m.raza LIKE %s OR m.ubicacion LIKE %s OR m.descripcion LIKE %s)"
        )
        parametros.extend([f"%{busqueda}%"] * 4)

    if estado:
        condiciones.append("m.estado = %s")
        parametros.append(estado)

    if especie:
        condiciones.append("m.especie = %s")
        parametros.append(especie)

    where = " AND ".join(condiciones)

    if where:
        where = "WHERE " + where

    consulta = f"""
        SELECT
            m.id_mascota AS id_publicacion,
            m.id_usuario AS usuario_id,
            u.nombre AS usuario,
            u.foto_perfil AS foto_usuario,
            m.nombre,
            m.descripcion,
            m.especie,
            m.raza,
            m.estado,
            m.ubicacion,
            m.foto,
            DATE_FORMAT(m.fecha, '%%d/%%m/%%Y') AS fecha,
            DATE_FORMAT(m.fecha_registro, '%%Y-%%m-%%d %%H:%%i:%%s') AS fecha_publicacion,
            (SELECT COUNT(*) FROM reacciones r WHERE r.id_publicacion = m.id_mascota) AS reacciones,
            (SELECT COUNT(*) FROM comentarios c WHERE c.id_publicacion = m.id_mascota) AS comentarios
        FROM mascotas m
        JOIN usuarios u ON u.id_usuario = m.id_usuario
        {where}
        ORDER BY m.fecha_registro DESC
    """

    mysql = conectar_bd()

    publicaciones = mysql.query_db(consulta, parametros)

    if not publicaciones:
        publicaciones = []

    for publicacion in publicaciones:
        publicacion["tiempo"] = tiempo_relativo(
            publicacion.get("fecha_publicacion")
        )

    total_publicaciones = len(publicaciones)

    total_mascotas = mysql.query_db(
        "SELECT COUNT(*) AS total FROM mascotas"
    ) or [{"total": 0}]

    total_usuarios = mysql.query_db(
        "SELECT COUNT(*) AS total FROM usuarios"
    ) or [{"total": 0}]

    return render_template(
        "murocomunitario.html",
        publicaciones=publicaciones,
        total_publicaciones=total_publicaciones,
        total_mascotas=total_mascotas[0]["total"],
        total_usuarios=total_usuarios[0]["total"]
    )


@app.route("/publicacion/<int:id_publicacion>/reaccionar", methods=["POST"])
def reaccionar_publicacion(id_publicacion):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mysql.query_db(
        """
        INSERT IGNORE INTO reacciones (id_publicacion, id_usuario)
        VALUES (%s, %s)
        """,
        (id_publicacion, session["usuario_id"])
    )

    return redirect(url_for("murocomunitario"))


@app.route("/publicacion/<int:id_publicacion>/comentar", methods=["POST"])
def comentar_publicacion(id_publicacion):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    comentario = request.form.get("comentario", "").strip()

    if comentario:

        mysql = conectar_bd()

        mysql.query_db(
            """
            INSERT INTO comentarios (id_publicacion, id_usuario, comentario)
            VALUES (%s, %s, %s)
            """,
            (id_publicacion, session["usuario_id"], comentario)
        )

    return redirect(url_for("murocomunitario"))


# =========================================================
# CHAT
# =========================================================

def cerrar_conversaciones_mascota(mysql, id_mascota):

    mysql.query_db(
        """
        UPDATE conversaciones SET estado = 'Cerrada', fecha_cierre = NOW()
        WHERE id_mascota = %s AND estado = 'Activa'
        """,
        (id_mascota,)
    )


def datos_conversacion(mysql, id_chat, usuario_id):

    conversacion = mysql.query_db(
        """
        SELECT c.id_chat, c.estado,
            IF(c.usuario_1 = %s, u2.nombre, u1.nombre) AS nombre,
            IF(c.usuario_1 = %s, u2.foto_perfil, u1.foto_perfil) AS foto,
            u1.id_usuario AS usuario_1,
            u2.id_usuario AS usuario_2
        FROM conversaciones c
        JOIN usuarios u1 ON u1.id_usuario = c.usuario_1
        JOIN usuarios u2 ON u2.id_usuario = c.usuario_2
        WHERE c.id_chat = %s
        """,
        (usuario_id, usuario_id, id_chat)
    )

    if not conversacion:
        return None

    return conversacion[0]


@app.route("/chat")
def chat():

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    usuario_id = session["usuario_id"]
    id_chat = request.args.get("id_chat", type=int)
    id_mascota = request.args.get("id_mascota", type=int)
    id_publicacion = request.args.get("id_publicacion", type=int)

    if not id_mascota:
        id_mascota = id_publicacion

    mysql = conectar_bd()

    conversaciones = mysql.query_db(
        """
        SELECT c.id_chat,
            IF(c.usuario_1 = %s, u2.nombre, u1.nombre) AS nombre,
            IF(c.usuario_1 = %s, u2.foto_perfil, u1.foto_perfil) AS foto,
            (SELECT mensaje FROM mensajes m
                WHERE m.id_chat = c.id_chat
                ORDER BY m.id_mensaje DESC LIMIT 1) AS ultimo_mensaje,
            (SELECT DATE_FORMAT(m.fecha, '%%H:%%i')
                FROM mensajes m
                WHERE m.id_chat = c.id_chat
                ORDER BY m.id_mensaje DESC LIMIT 1) AS hora
        FROM conversaciones c
        WHERE c.usuario_1 = %s OR c.usuario_2 = %s
        ORDER BY c.fecha_creacion DESC
        """,
        (usuario_id, usuario_id, usuario_id, usuario_id)
    )

    if not conversaciones:
        conversaciones = []

    mensajes = []
    chat_actual = {
        "id_chat": 0,
        "nombre": "Selecciona una conversación",
        "foto": None,
        "estado": "Activa"
    }

    if id_mascota:

        mascota = mysql.query_db(
            "SELECT id_mascota, id_usuario FROM mascotas WHERE id_mascota = %s",
            (id_mascota,)
        )

        if not mascota:
            flash("No se encontró esa mascota.", "error")
            return redirect(url_for("murocomunitario"))

        dueno = mascota[0]["id_usuario"]

        if dueno == usuario_id:
            flash("No puedes contactarte contigo mismo.", "error")
            return redirect(url_for("murocomunitario"))

        existente = mysql.query_db(
            """
            SELECT id_chat FROM conversaciones
            WHERE id_mascota = %s
                AND ((usuario_1 = %s AND usuario_2 = %s)
                    OR (usuario_1 = %s AND usuario_2 = %s))
            LIMIT 1
            """,
            (id_mascota, usuario_id, dueno, dueno, usuario_id)
        )

        if existente:
            id_chat = existente[0]["id_chat"]
        else:
            id_chat = mysql.query_db(
                """
                INSERT INTO conversaciones (id_mascota, usuario_1, usuario_2, estado)
                VALUES (%s, %s, %s, 'Activa')
                """,
                (id_mascota, usuario_id, dueno)
            )

        return redirect(url_for("chat", id_chat=id_chat))

    if id_chat:

        conversacion = datos_conversacion(mysql, id_chat, usuario_id)

        if not conversacion:
            flash("No tienes acceso a esa conversación.", "error")
            return redirect(url_for("chat"))

        if (
            conversacion["usuario_1"] != usuario_id
            and conversacion["usuario_2"] != usuario_id
        ):
            flash("No tienes acceso a esa conversación.", "error")
            return redirect(url_for("chat"))

        mensajes = mysql.query_db(
            """
            SELECT id_usuario, mensaje, imagen, ubicacion,
                DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i') AS hora
            FROM mensajes
            WHERE id_chat = %s
            ORDER BY id_mensaje
            """,
            (id_chat,)
        )

        if not mensajes:
            mensajes = []

        chat_actual = {
            "id_chat": conversacion["id_chat"],
            "nombre": conversacion["nombre"],
            "foto": conversacion["foto"],
            "estado": conversacion["estado"]
        }

    return render_template(
        "chat.html",
        conversaciones=conversaciones,
        mensajes=mensajes,
        chat_actual=chat_actual
    )


@app.route("/chat/<int:id_chat>/enviar", methods=["POST"])
def enviar_mensaje(id_chat):

    bloqueo = requiere_sesion()

    if bloqueo:
        return bloqueo

    usuario_id = session["usuario_id"]
    mensaje_texto = request.form.get("mensaje", "").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    imagen = request.files.get("imagen")

    mysql = conectar_bd()

    conversacion = datos_conversacion(mysql, id_chat, usuario_id)

    if not conversacion:
        flash("No tienes acceso a esa conversación.", "error")
        return redirect(url_for("chat"))

    if (
        conversacion["usuario_1"] != usuario_id
        and conversacion["usuario_2"] != usuario_id
    ):
        flash("No tienes acceso a esa conversación.", "error")
        return redirect(url_for("chat"))

    if conversacion["estado"] == "Cerrada":
        flash("Esta conversación está cerrada.", "error")
        return redirect(url_for("chat", id_chat=id_chat))

    imagen_guardada = None

    if imagen and imagen.filename != "":
        imagen_guardada = nombre_archivo_unico(imagen)

    if not mensaje_texto and not imagen_guardada:
        return redirect(url_for("chat", id_chat=id_chat))

    mysql.query_db(
        """
        INSERT INTO mensajes (id_chat, id_usuario, mensaje, imagen, ubicacion)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (id_chat, usuario_id, mensaje_texto, imagen_guardada, ubicacion)
    )

    return redirect(url_for("chat", id_chat=id_chat))


# =========================================================
# PANEL ADMINISTRADOR
# =========================================================

@app.route("/administrador")
def paneladministrador():

    bloqueo = requiere_admin()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    total_usuarios = mysql.query_db(
        "SELECT COUNT(*) AS total FROM usuarios"
    ) or [{"total": 0}]

    total_mascotas = mysql.query_db(
        "SELECT COUNT(*) AS total FROM mascotas"
    ) or [{"total": 0}]

    total_reportes = mysql.query_db(
        """
        SELECT COUNT(*) AS total FROM mascotas
        WHERE estado IN ('Perdida', 'Avistamiento')
        """
    ) or [{"total": 0}]

    total_reunidas = mysql.query_db(
        "SELECT COUNT(*) AS total FROM mascotas WHERE estado = 'Encontrada'"
    ) or [{"total": 0}]

    usuarios = mysql.query_db(
        """
        SELECT id_usuario, nombre, apellido, correo, comuna, rol, estado,
            foto_perfil, DATE_FORMAT(fecha_registro, '%%d/%%m/%%Y') AS fecha_registro
        FROM usuarios
        ORDER BY id_usuario
        """
    )

    if not usuarios:
        usuarios = []

    mascotas = mysql.query_db(
        """
        SELECT m.id_mascota, m.nombre, m.especie, m.raza, m.estado,
            m.ubicacion, m.codigo, m.foto, u.nombre AS propietario,
            u.id_usuario AS id_propietario
        FROM mascotas m
        JOIN usuarios u ON u.id_usuario = m.id_usuario
        ORDER BY m.fecha_registro DESC
        """
    )

    if not mascotas:
        mascotas = []

    reportes_moderacion = [m for m in mascotas if m["estado"] != "Encontrada"]

    publicaciones_recientes = mascotas[:5]

    return render_template(
        "paneladministrador.html",
        usuarios=usuarios,
        mascotas=mascotas,
        total_usuarios=total_usuarios[0]["total"],
        total_mascotas=total_mascotas[0]["total"],
        total_reportes=total_reportes[0]["total"],
        total_reunidas=total_reunidas[0]["total"],
        reportes_moderacion=reportes_moderacion,
        publicaciones_recientes=publicaciones_recientes
    )


@app.route("/administrador/usuario/<int:id_usuario>/bloquear", methods=["POST"])
def bloquear_usuario(id_usuario):

    bloqueo = requiere_admin()

    if bloqueo:
        return bloqueo

    if id_usuario == session["usuario_id"]:
        flash("No puedes bloquear tu propia cuenta.", "error")
        return redirect(url_for("paneladministrador"))

    mysql = conectar_bd()

    mysql.query_db(
        "UPDATE usuarios SET estado = 'Bloqueado' WHERE id_usuario = %s",
        (id_usuario,)
    )

    flash("Usuario bloqueado.", "exito")
    return redirect(url_for("paneladministrador"))


@app.route("/administrador/usuario/<int:id_usuario>/activar", methods=["POST"])
def activar_usuario(id_usuario):

    bloqueo = requiere_admin()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mysql.query_db(
        "UPDATE usuarios SET estado = 'Activo' WHERE id_usuario = %s",
        (id_usuario,)
    )

    flash("Usuario activado.", "exito")
    return redirect(url_for("paneladministrador"))


@app.route("/administrador/reporte/<int:id_mascota>/revisar")
def revisar_reporte_admin(id_mascota):

    bloqueo = requiere_admin()

    if bloqueo:
        return bloqueo

    return redirect(url_for("detalle_mascota", id_mascota=id_mascota))


@app.route("/administrador/reporte/<int:id_mascota>/eliminar", methods=["POST"])
def eliminar_reporte_admin(id_mascota):

    bloqueo = requiere_admin()

    if bloqueo:
        return bloqueo

    mysql = conectar_bd()

    mysql.query_db(
        "DELETE FROM mascotas WHERE id_mascota = %s",
        (id_mascota,)
    )

    flash("Reporte eliminado.", "exito")
    return redirect(url_for("paneladministrador"))


if __name__ == "__main__":
    app.run(debug=True)