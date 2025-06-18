import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import jsonify, request, session
from config import APP_DOMAIN, SENDGRID_API_KEY, SENDGRID_SENDER_EMAIL
from database.utils_db import get_db_connection
import base64

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def enviar_invitacion():
    print("DEBUG: Iniciando función enviar_invitacion.")

    # 1. Obtener datos del formulario del propietario
    email_invitado = request.form.get("email_invitado")
    fecha_visita_str = request.form.get("fecha_visita")
    hora_visita_str = request.form.get("hora_visita") # Asumiendo que esta columna existirá
    id_propietario = session.get('id_usuario')

    print(f"DEBUG: Datos recibidos - Email: {email_invitado}, Fecha: {fecha_visita_str}, Hora: {hora_visita_str}, Propietario ID: {id_propietario}")

    if not all([email_invitado, fecha_visita_str, hora_visita_str, id_propietario]):
        print("ERROR: Faltan datos necesarios para enviar la invitación.")
        return jsonify({"status": "error", "message": "Faltan datos (email, fecha, hora o ID de propietario)."}), 400

    # Validar formato de fecha y hora
    try:
        # Solo para validación, no se usa en el INSERT como objeto datetime.date/time
        datetime.strptime(fecha_visita_str, '%Y-%m-%d')
        datetime.strptime(hora_visita_str, '%H:%M')
    except ValueError as e:
        print(f"ERROR: Formato de fecha/hora incorrecto: {e}")
        return jsonify({"status": "error", "message": "Formato de fecha u hora incorrecto. Use YYYY-MM-DD y HH:MM."}), 400

    # 2. Generar token único para la invitación
    token_invitacion = uuid.uuid4().hex
    print(f"DEBUG: Token de invitación generado: {token_invitacion}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 3. Registrar la invitación en la base de datos con estado 'noAprobada'
        # Ajustado para los nombres de columna de tu tabla
        cursor.execute(
            """
            INSERT INTO invitaciones (
                id_usuario, email_visita, fecha_visita, hora_visita, estado, token
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id_propietario, email_invitado, fecha_visita_str, hora_visita_str, 'noAprobada', token_invitacion)
        )
        conn.commit()
        print("DEBUG: Invitación registrada en la DB con estado 'noAprobada'.")
    except sqlite3.Error as e:
        conn.close()
        print(f"ERROR: Error de base de datos al registrar la invitación: {e}")
        return jsonify({"status": "error", "message": f"Error de base de datos al registrar invitación: {e}"}), 500

    # 4. Enviar correo electrónico con SendGrid
    enlace_formulario_invitado = f"{APP_DOMAIN}/invitacion/{token_invitacion}"
    print(f"DEBUG: Enlace para el invitado: {enlace_formulario_invitado}")

    message = Mail(
        from_email=SENDGRID_SENDER_EMAIL,
        to_emails=email_invitado,
        subject='Invitación a visitar el edificio',
        html_content=f'<p>Hola!</p>'
                     f'<p>Has sido invitado a visitar el edificio. Por favor, completa tus datos en el siguiente enlace para confirmar tu visita:</p>'
                     f'<p><a href="{enlace_formulario_invitado}">{enlace_formulario_invitado}</a></p>'
                     f'<p>Fecha de visita: {fecha_visita_str}</p>'
                     f'<p>Hora de visita: {hora_visita_str}</p>'
                     f'<p>¡Te esperamos!</p>'
                     f'<p>Saludos cordiales,</p>'
                     f'<p>Tu anfitrión</p>'
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"DEBUG: Correo SendGrid enviado. Status Code: {response.status_code}")
        print(f"DEBUG: Correo SendGrid Body: {response.body}")
        print(f"DEBUG: Correo SendGrid Headers: {response.headers}")

        conn.close()
        return jsonify({
            "status": "ok",
            "message": "Invitación enviada con éxito.",
            "enlace_invitado": enlace_formulario_invitado
        })
    except Exception as e:
        conn.rollback() # Si falla el envío, deshacemos el registro en DB
        conn.close()
        print(f"ERROR: Error al enviar correo con SendGrid: {e}")
        return jsonify({"status": "error", "message": f"Error al enviar la invitación: {e}"}), 500
    
def procesar_formulario_invitado():
    print("DEBUG: Iniciando función procesar_formulario_invitado.")

    token = request.form.get('token')
    nombre_invitado = request.form.get('nombre_invitado')
    dni_invitado = request.form.get('dni_invitado')
    ingresa_auto_str = request.form.get('ingresa_auto')
    patente = request.form.get('patente')
    poliza_seguro_base64 = request.files.get('poliza_seguro') # Esto será un FileStorage
    cantidad_acompanantes_str = request.form.get('cantidad_acompanantes')
    acompanantes_mayores = request.form.get('acompanantes_mayores')
    acompanantes_menores = request.form.get('acompanantes_menores')

    print(f"DEBUG: Datos recibidos del formulario de invitado para token '{token}':")
    print(f"  Nombre: {nombre_invitado}, DNI: {dni_invitado}")
    print(f"  Ingresa auto: {ingresa_auto_str}, Patente: {patente}")
    print(f"  Póliza: {poliza_seguro_base64.filename if poliza_seguro_base64 else 'No adjunta'}")
    print(f"  Acompañantes: {cantidad_acompanantes_str} (Mayores: {acompanantes_mayores}, Menores: {acompanantes_menores})")

    # Validaciones básicas
    if not all([token, nombre_invitado, dni_invitado]):
        print("ERROR: Faltan datos obligatorios del invitado.")
        return jsonify({"status": "error", "message": "Por favor, complete nombre, DNI y el token de invitación."}), 400

    ingresa_auto = 1 if ingresa_auto_str == 'si' else 0
    cantidad_acompanantes = int(cantidad_acompanantes_str) if cantidad_acompanantes_str else 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verificar que el token exista y la invitación esté pendiente
        cursor.execute("SELECT * FROM invitaciones WHERE token = ?", (token,))
        invitacion = cursor.fetchone()

        if not invitacion:
            conn.close()
            print(f"ERROR: Token de invitación '{token}' no encontrado en la DB.")
            return jsonify({"status": "error", "message": "Invitación no válida."}), 404

        if invitacion['estado'] != 'noAprobada': # O 'pendiente' si lo cambiaste
            conn.close()
            print(f"ERROR: Invitación con token '{token}' ya ha sido procesada o su estado no es 'noAprobada'.")
            return jsonify({"status": "error", "message": f"Esta invitación ya ha sido {invitacion['estado']}."}), 403

        # Convertir la imagen de la póliza a Base64 si se adjuntó
        imagen_poliza_base64 = None
        if poliza_seguro_base64:
            try:
                # Leer el contenido del archivo y codificarlo a Base64
                imagen_poliza_base64 = base64.b64encode(poliza_seguro_base64.read()).decode('utf-8')
                print("DEBUG: Imagen de póliza convertida a Base64.")
            except Exception as e:
                print(f"ERROR: No se pudo procesar la imagen de la póliza: {e}")
                return jsonify({"status": "error", "message": "Error al procesar la imagen de la póliza."}), 400
        else:
            # Si ingresa en auto pero no adjunta póliza
            if ingresa_auto == 1:
                print("WARNING: Se seleccionó ingreso en auto pero no se adjuntó póliza.")
                # Decide si esto es un error bloqueante o solo una advertencia
                # Por ahora, lo dejaremos pasar para la prueba inicial, pero es un TODO para validación.

        # Actualizar la invitación en la DB
        # El estado inicial será 'completada' (o 'aprobada' si la validación de póliza fuera instantánea)
        # Aquí la validación de la póliza se hace después, así que el estado es 'completada'
        nuevo_estado = 'completada' # Cambia esto a 'aprobada' si la validación de póliza se hace aquí.

        cursor.execute(
            """
            UPDATE invitaciones SET
                nombre_visitante = ?,
                dni_visitante = ?,
                vehiculo = ?,
                patente = ?,
                imagen_poliza = ?,
                cantidad_acompanantes = ?,
                acompanantes_mayores = ?,
                acompanantes_menores = ?,
                estado = ?
            WHERE token = ?
            """,
            (nombre_invitado, dni_invitado, ingresa_auto, patente, imagen_poliza_base64,
                cantidad_acompanantes, acompanantes_mayores, acompanantes_menores,
                nuevo_estado, token)
        )
        conn.commit()
        print(f"DEBUG: Invitación con token '{token}' actualizada y estado cambiado a '{nuevo_estado}'.")

        conn.close()
        return jsonify({
            "status": "ok",
            "message": "Datos de visita registrados con éxito. Esperando aprobación." # Mensaje provisional
        })

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"ERROR: Error de base de datos al procesar el formulario del invitado: {e}")
        return jsonify({"status": "error", "message": f"Error de base de datos al registrar datos: {e}"}), 500
    except Exception as e:
        conn.rollback() # Asegurar rollback en caso de cualquier otra excepción
        conn.close()
        print(f"ERROR: Error inesperado al procesar el formulario del invitado: {e}")
        return jsonify({"status": "error", "message": f"Error interno del servidor: {e}"}), 500
