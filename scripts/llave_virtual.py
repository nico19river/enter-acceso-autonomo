# TODO ESCALABILIDAD Y MANTENIMIeNTO: separar la logica de cada metodo en archivos separados 
# TODO agregar una funcion global con la coneccion a DB o buscar la que hizo nico :P
# Lógica base por Nico Beltran. - Integración  May Artoni

import sqlite3
import uuid
import io
import base64
from datetime import datetime, timedelta
from flask import jsonify, request, session
import qrcode
from config import APP_DOMAIN
from database.utils_db import get_db_connection

# - NB
def _verificar_pin_usuario(usuario, pin_ingresado):
    print(f"DEBUG: Verificando PIN para usuario {usuario['id_usuario']}.")
    print(f"DEBUG: PIN ingresado: '{pin_ingresado}', PIN de acceso: '{usuario['pin_acceso']}', PIN de seguridad: '{usuario['pin_seguridad']}'")
    if pin_ingresado == usuario["pin_acceso"]:  
        print("DEBUG: PIN ingresado es VÁLIDO.")
        return "valido"
    elif pin_ingresado == usuario["pin_seguridad"]:
        print("DEBUG: PIN ingresado es de SEGURIDAD.")
        return "seguridad"
    else:
        print("DEBUG: PIN ingresado es INCORRECTO.")
        return "incorrecto"

# -MA
def generar_qr_base64(url):
   print(f"DEBUG: Generando QR para URL: {url}")
   # Crear el objeto QR y añadir la URL
   qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
   qr.add_data(url)
   qr.make(fit=True)

    # Crear la imagen y guardarla en un buffer en memoria
   img = qr.make_image(fill_color="black", back_color="white")
   buf = io.BytesIO()
   img.save(buf, format="PNG")
    
    # retorna la imagen en formato texto Base64
   print("DEBUG: QR generado en Base64.")
   return base64.b64encode(buf.getvalue()).decode('utf-8')

# TODO hacer esta funcion, esta es solo una version de prueba
def _enviar_alerta_silenciosa(usuario, conn):
    print(f"\n--- SIMULACIÓN DE ALERTA SILENCIOSA para usuario {usuario['id_usuario']} ---") #mejorar esto
    # Aquí iría la lógica real para enviar la alerta (ej. correo, notificación, etc.)

def generar_llave_virtual():
    print("DEBUG: Iniciando función generar_llave_virtual.")
    print(f"DEBUG: Request form data: {request.form}") # Muestra todos los datos del formulario

    id_usuario = request.form.get("id_usuario") 
    pin_ingresado = request.form.get("pin_ingresado")

    print(f"DEBUG: id_usuario recibido: '{id_usuario}', pin_ingresado recibido: '{pin_ingresado}'")

    if not id_usuario or not pin_ingresado:
        print("ERROR: Faltan datos (id_usuario o pin_ingresado).")
        return jsonify({"status": "error", "message": "Faltan datos (id_usuario o PIN ingresado)."}), 400

    # coneccion a la DB - NB
    conn = get_db_connection() # FUNCION GLOBAL RASTREAR
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por su nombre.
    cursor = conn.cursor()
    print("DEBUG: Conexión a la base de datos establecida.")

    
    # selecciona el usuario - NB
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    usuario = cursor.fetchone()

    # verificar Usuario existente - NB
    if not usuario:
        conn.close()
        print(f"ERROR: Usuario con ID '{id_usuario}' no encontrado en la DB.")
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    
    print(f"DEBUG: Usuario encontrado: {dict(usuario)}") # Muestra los datos del usuario como un diccionario

    # Verificar si la cuenta del usuario está bloqueada - NB
    if usuario["bloqueado"]:
        conn.close()
        print(f"ERROR: Usuario '{id_usuario}' está bloqueado.")
        return jsonify({"status": "error", "message": "Este usuario se encuentra bloqueado"}), 403

    estado_pin = _verificar_pin_usuario(usuario, pin_ingresado)
    print(f"DEBUG: Estado del PIN verificado: {estado_pin}")

    # Guarda el token y validez de el QR en tabla llaves_virtuales para facilitar luego su lectura - MA
    if estado_pin in ["valido", "seguridad"]:
        token = uuid.uuid4().hex # Genera un token único.
        fecha_exp = datetime.now() + timedelta(hours=1) # El QR es válido por 1 hora
        print(f"DEBUG: PIN '{estado_pin}'. Generando token '{token}' con fecha de expiración: {fecha_exp.isoformat()}")

        try:
            # Insertamos la nueva llave en nuestra tabla con las llavesQR
            cursor.execute(
                "INSERT INTO llaves_virtuales (id_usuario, token, fecha_expiracion) VALUES (?, ?, ?)",
                (id_usuario, token, fecha_exp.isoformat())
            )
            # Reseteamos los intentos fallidos (solo se ejecuta en cuando el pin es valido)
            cursor.execute("UPDATE usuarios SET intentos_fallidos = 0 WHERE id_usuario = ?", (id_usuario,))
            conn.commit()
            print("DEBUG: Llave virtual insertada y intentos fallidos reseteados en DB. Commit exitoso.")
        except sqlite3.Error as e:
            conn.close()
            print(f"ERROR: Error de base de datos al insertar llave virtual o resetear intentos: {e}")
            return jsonify({"status": "error", "message": f"Error de base de datos: {e}"}), 500

        # generar un QR en base64 - MA
        url_para_qr = f"{APP_DOMAIN}/validar-llave/{token}"
        print(f"DEBUG: URL para QR: {url_para_qr}")
        qr_base64 = generar_qr_base64(url_para_qr)
        
        # Enviar alerta silenciosa si se usó el PIN de seguridad - MA
        if estado_pin == "seguridad":
            _enviar_alerta_silenciosa(usuario, conn)
            print("DEBUG: Se activó protocolo de alerta silenciosa.")

        conn.close() #cerrar conexion
        print("DEBUG: Conexión a la DB cerrada. Devolviendo respuesta exitosa.")
        return jsonify({
            "status": "ok",
            "message": "Llave virtual generada.",
            "qr": qr_base64, # La imagen del QR en base64
            "alerta": (estado_pin == "seguridad") #pregunta si es true o false, es una flag para poder llamarla en caso de que sea true
        })

    else: # PIN Incorrecto
        print("DEBUG: PIN INCORRECTO. Gestionando intentos fallidos.")
        # contador intentos fallidos, cuando hay 3 intentos fallido bloquea la llave
        intentos_actuales = usuario["intentos_fallidos"] + 1
        se_bloquea = 1 if intentos_actuales >= 3 else 0
        print(f"DEBUG: Intentos fallidos actuales: {intentos_actuales}. ¿Se bloquea?: {bool(se_bloquea)}")

        try:
            # 3. Actualizar la base de datos con los nuevos valores.
            cursor.execute(
                "UPDATE usuarios SET intentos_fallidos = ?, bloqueado = ? WHERE id_usuario = ?",
                (intentos_actuales, se_bloquea, usuario["id_usuario"])
            )
            conn.commit()
            print("DEBUG: Intentos fallidos y estado de bloqueo actualizados en DB. Commit exitoso.")
        except sqlite3.Error as e:
            conn.close()
            print(f"ERROR: Error de base de datos al actualizar intentos fallidos: {e}")
            # Si hay un error de DB,  código 500 (Error del Servidor).
            return jsonify({"status": "error", "message": f"Error de base de datos al actualizar intentos: {e}"}), 500
        
        conn.close()
        print("DEBUG: Conexión a la DB cerrada.")

        # 4. Devolver la respuesta adecuada al frontend.
        if se_bloquea:
            print("DEBUG: Usuario bloqueado por exceder intentos fallidos.")
            return jsonify({
                "status": "error", 
                "message": "LLAVE BLOQUEADA / COMUNÍQUESE CON ADMINISTRACIÓN / PARA INGRESAR DIRIGIRSE A LA ENTRADA MANUAL"
            }), 403 #forviden
        else:
            intentos_restantes = 3 - intentos_actuales
            print(f"DEBUG: PIN incorrecto. Quedan {intentos_restantes} intento(s).")
            return jsonify({
                "status": "error", 
                "message": f"PIN incorrecto. Le quedan {intentos_restantes} intento(s)."
            }), 401 #unauthorized
