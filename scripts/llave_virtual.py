# TODO ESCALABILIDAD Y MANTENIMIeNTO: separar la logica de cada metodo en archivos separados 
# TODO agregar una funcion global con la coneccion a DB o buscar la que hizo nico :P
# Lógica base por Nico Beltran. - Integración  May Artoni

import sqlite3
import uuid
import io
import base64
from datetime import datetime, timedelta
from flask import jsonify, request  
import qrcode
from config import APP_DOMAIN
from database.utils_db import get_db_connection

# - NB
def _verificar_pin_usuario(usuario, pin_ingresado):
    if pin_ingresado == usuario["pin_acceso"]:  
        return "valido"
    elif pin_ingresado == usuario["pin_seguridad"]:
        return "seguridad"
    else:
        return "incorrecto"

# -MA
def generar_qr_base64(url):
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
    
    # retorna la imagen en formato texto Base94
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# TODO hacer esta funcion, esta es solo una version de prueba
def _enviar_alerta_silenciosa(usuario, conn):
    print("\n--- SIMULACIÓN DE ALERTA SILENCIOSA ---") #mejorar esto

def generar_llave_virtual():
    
    id_usuario = request.form.get("id_usuario") 
    pin_ingresado = request.form.get("pin_ingresado")

    if not id_usuario or not pin_ingresado:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    #coneccion a la DB - NB
    conn = get_db_connection() # FUNCION GLOBAL RASTREAR
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por su nombre.
    cursor = conn.cursor()

    
    #selecciona el usuario - NB
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    usuario = cursor.fetchone()

    #verificar Usuario existente - NB
    if not usuario:
        conn.close()
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    # Verificar si la cuenta del usuario está bloqueada - NB
    if usuario["bloqueado"]:
        conn.close()
        return jsonify({"status": "error", "message": "Este usuario se encuentra bloqueado"}), 403

    estado_pin = _verificar_pin_usuario(usuario, pin_ingresado)

    # Guarda el token y validez de el QR en tabla llaves_virtuales para facilitar luego su lectura - MA
    if estado_pin in ["valido", "seguridad"]: #mantiene experiencia de usuario, genera el QR en ambos casos, pero en caso de pin de seguridad se activa protocolo de seguridad
        token = uuid.uuid4().hex # Genera un token único.
        fecha_exp = datetime.now() + timedelta(hours=1) # El QR es válido por 1 hora

        try:
            # Insertamos la nueva llave en nuestra tabla con las llavesQR
            cursor.execute(
                "INSERT INTO llaves_virtuales (id_usuario, token, fecha_expiracion) VALUES (?, ?, ?)",
                (id_usuario, token, fecha_exp.isoformat())
            )
            # Reseteamos los intentos fallidos (solo se ejecuta en cuando el pin es valido)
            cursor.execute("UPDATE usuarios SET intentos_fallidos = 0 WHERE id_usuario = ?", (id_usuario,))
            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            return jsonify({"status": "error", "message": f"Error de base de datos: {e}"}), 500

        # generar un QR en base64 - MA
        
        url_para_qr = f"{APP_DOMAIN}/validar-llave/{token}"
        qr_base64 = generar_qr_base64(url_para_qr)
        
        # Enviar alerta silenciosa si se usó el PIN de seguridad - MA
        if estado_pin == "seguridad":
            _enviar_alerta_silenciosa(usuario, conn)

        conn.close() #cerrar conexion
        
        return jsonify({
            "status": "ok",
            "message": "Llave virtual generada.",
            "qr": qr_base64, # La imagen del QR en base64
            "alerta": (estado_pin == "seguridad") #pregunta si es true o false, es una flag para poder llamarla en caso de que sea true
        })

    else: # PIN Incorrecto
        
        # contador intentos fallidos, cuando hay 3 intentos fallido bloquea la llave
        intentos_actuales = usuario["intentos_fallidos"] + 1
        se_bloquea = 1 if intentos_actuales >= 3 else 0

        try:
            # 3. Actualizar la base de datos con los nuevos valores.
            cursor.execute(
                "UPDATE usuarios SET intentos_fallidos = ?, bloqueado = ? WHERE id_usuario = ?",
                (intentos_actuales, se_bloquea, usuario["id_usuario"])
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            # Si hay un error de DB,  código 500 (Error del Servidor).
            return jsonify({"status": "error", "message": f"Error de base de datos al actualizar intentos: {e}"}), 500
        
        conn.close()

        # 4. Devolver la respuesta adecuada al frontend.
        if se_bloquea:
            
            return jsonify({
                "status": "error", 
                "message": "LLAVE BLOQUEADA / COMUNÍQUESE CON ADMINISTRACIÓN / PARA INGRESAR DIRIGIRSE A LA ENTRADA MANUAL"
            }), 403 #forviden
        else:
            
            intentos_restantes = 3 - intentos_actuales
            return jsonify({
                "status": "error", 
                "message": f"PIN incorrecto. Le quedan {intentos_restantes} intento(s)."
            }), 401 #unauthorized

 
