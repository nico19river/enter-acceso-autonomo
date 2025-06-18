import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import jsonify, request, session
from config import APP_DOMAIN, SENDGRID_API_KEY, SENDGRID_SENDER_EMAIL
from database.utils_db import get_db_connection
import base64
from scripts.utils_ocr import validar_poliza_automaticamente
import io
from sendgrid import SendGridAPIClient
import qrcode
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId # <--- NUEVAS IMPORTACIONES

def generar_qr_base64(url):
    print(f"DEBUG: Generando QR para URL: {url}")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    
    # --- DEBUGGING ADICIONAL ---
    try:
        img.save(buf, format="PNG")
        print("DEBUG: Imagen QR guardada en buffer en formato PNG.")
    except Exception as e:
        # Aunque aquí hay un error, el return original no lo manejaba explícitamente
        # y simplemente seguiría. Para depuración, imprimimos el error.
        print(f"ERROR: Falló al guardar la imagen QR en el buffer: {e}")
        # NO CAMBIAMOS EL RETURN A CADENA VACÍA AQUÍ, MANTENEMOS EL COMPORTAMIENTO ORIGINAL
        # Si buf.getvalue() fuera un problema, el b64encode lanzaría una excepción.
    # -----------------------------

    base64_string = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # --- DEBUGGING ADICIONAL ---
    if base64_string:
        print(f"DEBUG: QR generado en Base64. Longitud: {len(base64_string)} caracteres.")
        print(f"DEBUG: Primeros 50 caracteres del Base64: {base64_string[:50]}...")
    else:
        print("ERROR: La cadena Base64 del QR está vacía después de la codificación.")
    # -----------------------------

    return base64_string

def enviar_invitacion():
    print("DEBUG: Iniciando función enviar_invitacion.")

    # 1. Obtener datos del formulario del propietario
    email_visita = request.form.get("email_visita")
    fecha_visita_str = request.form.get("fecha_visita")
    hora_visita_str = request.form.get("hora_visita") # Asumiendo que esta columna existirá
    id_propietario = session.get('id_usuario')

    print(f"DEBUG: Datos recibidos - Email: {email_visita}, Fecha: {fecha_visita_str}, Hora: {hora_visita_str}, Propietario ID: {id_propietario}")

    if not all([email_visita, fecha_visita_str, hora_visita_str, id_propietario]):
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
            (id_propietario, email_visita, fecha_visita_str, hora_visita_str, 'noAprobada', token_invitacion)
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
        to_emails=email_visita,
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

    token_invitacion = request.form.get('token')
    nombre_invitado = request.form.get('nombre_invitado')
    dni_invitado = request.form.get('dni_invitado')
    ingresa_auto_str = request.form.get('ingresa_auto')
    patente = request.form.get('patente')
    poliza_seguro_file = request.files.get('poliza_seguro')
    cantidad_acompanantes_str = request.form.get('cantidad_acompanantes')
    acompanantes_mayores = request.form.get('acompanantes_mayores')
    acompanantes_menores = request.form.get('acompanantes_menores')

    print(f"DEBUG: Datos recibidos del formulario de invitado para token '{token_invitacion}':")
    print(f"  Nombre: {nombre_invitado}, DNI: {dni_invitado}")
    print(f"  Ingresa auto: {ingresa_auto_str}, Patente: {patente}")
    print(f"  Póliza: {poliza_seguro_file.filename if poliza_seguro_file else 'No adjunta'}")
    print(f"  Acompañantes: {cantidad_acompanantes_str} (Mayores: {acompanantes_mayores}, Menores: {acompanantes_menores})")

    if not all([token_invitacion, nombre_invitado, dni_invitado]):
        print("ERROR: Faltan datos obligatorios del invitado.")
        return jsonify({"status": "error", "message": "Por favor, complete nombre, DNI y el token de invitación."}), 400

    ingresa_auto = 1 if ingresa_auto_str == 'si' else 0
    cantidad_acompanantes = int(cantidad_acompanantes_str) if cantidad_acompanantes_str else 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM invitaciones WHERE token = ?", (token_invitacion,))
        invitacion = cursor.fetchone()

        if not invitacion:
            conn.close()
            print(f"ERROR: Token de invitación '{token_invitacion}' no encontrado en la DB.")
            return jsonify({"status": "error", "message": "Invitación no válida."}), 404

        if invitacion['estado'] != 'noAprobada':
            conn.close()
            print(f"ERROR: Invitación con token '{token_invitacion}' ya ha sido procesada o su estado no es 'noAprobada'.")
            return jsonify({"status": "error", "message": f"Esta invitación ya ha sido {invitacion['estado']}."}), 403

        imagen_poliza_base64 = None
        poliza_validada_automaticamente = False
        validacion_automatica_mensaje = "No se requirió validación automática de póliza."
        
        qr_acceso_base64 = None

        if ingresa_auto == 1:
            if poliza_seguro_file:
                try:
                    poliza_bytes = poliza_seguro_file.read()
                    imagen_poliza_base64 = base64.b64encode(poliza_bytes).decode('utf-8')
                    print("DEBUG: Imagen de póliza convertida a Base64.")

                    # *** LLAMADA A LA FUNCIÓN DESDE EL NUEVO SCRIPT ***
                    poliza_validada_automaticamente, validacion_automatica_mensaje = validar_poliza_automaticamente(imagen_poliza_base64)
                    print(f"DEBUG: Resultado de validación automática: {poliza_validada_automaticamente}, Mensaje: {validacion_automatica_mensaje}")

                except Exception as e:
                    print(f"ERROR: No se pudo procesar o validar la imagen de la póliza con OCR: {e}")
                    validacion_automatica_mensaje = f"Error al procesar la póliza para validación: {e}"
            else:
                print("WARNING: Se seleccionó ingreso en auto pero no se adjuntó póliza.")
                validacion_automatica_mensaje = "Ingreso en auto seleccionado pero sin póliza adjunta."

        nuevo_estado = 'completada'
        mensaje_final = "Datos de visita registrados con éxito. Esperando aprobación."

        if ingresa_auto == 1 and poliza_validada_automaticamente:
            nuevo_estado = 'aprobada'
            mensaje_final = "Datos de visita registrados y póliza aprobada automáticamente. Enviando QR de acceso."
            print("DEBUG: Póliza aprobada automáticamente. Estado final: 'aprobada'.")
            
            enlace_acceso_qr = f"{APP_DOMAIN}/acceso/{token_invitacion}"
            qr_acceso_base64 = generar_qr_base64(enlace_acceso_qr)
            print(f"DEBUG: QR de acceso generado con enlace: {enlace_acceso_qr}")

        elif ingresa_auto == 1 and not poliza_validada_automaticamente:
            nuevo_estado = 'completada'
            mensaje_final = f"Datos de visita registrados. Póliza requiere revisión: {validacion_automatica_mensaje}"
            print(f"DEBUG: Póliza no aprobada automáticamente. Estado final: 'completada'. Mensaje: {validacion_automatica_mensaje}")
        elif ingresa_auto == 0:
            nuevo_estado = 'completada'
            mensaje_final = "Datos de visita registrados. No requiere validación de póliza."
            print("DEBUG: No se requiere póliza. Estado final: 'completada'.")


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
             nuevo_estado, token_invitacion)
        )
        conn.commit()
        print(f"DEBUG: Invitación con token '{token_invitacion}' actualizada y estado cambiado a '{nuevo_estado}'.")

        if nuevo_estado == 'aprobada' and qr_acceso_base64:
            email_destinatario = invitacion['email_visita']
            subject_email_qr = '¡Tu acceso ha sido aprobado!'
            html_content_qr = f'<p>Hola {nombre_invitado}!</p>' \
                              f'<p>¡Excelente noticia! Tu solicitud de visita para el {invitacion["fecha_visita"]} a las {invitacion["hora_visita"]} ha sido <strong>APROBADA</strong>.</p>' \
                              f'<p>Utiliza QR que adjuntamos para ingresar</p>' \
                              f'<p>¡Te esperamos!</p>' \
                              f'<p>Saludos,</p>' \
                              f'<p>enlace verificacion para test: <a href="{enlace_acceso_qr}">{enlace_acceso_qr}</a></p>' \
            
            message_qr = Mail(
                from_email=SENDGRID_SENDER_EMAIL,
                to_emails=email_destinatario,
                subject=subject_email_qr,
                html_content=html_content_qr
            )
            attachedFile = Attachment(
                FileContent(qr_acceso_base64),
                FileName('qr_acceso.png'), # Nombre del archivo para el adjunto
                FileType('image/png'),     # Tipo MIME del archivo
                Disposition('inline'),     # ¡CRÍTICO! 'inline' para que se muestre en el cuerpo del correo
                ContentId('qr_acceso_imagen') # ¡CRÍTICO! Este ID debe coincidir con el 'cid:' en el HTML
            )
            message_qr.attachment = attachedFile
            try:
                sg_qr = SendGridAPIClient(SENDGRID_API_KEY)
                response_qr = sg_qr.send(message_qr)
                print(f"DEBUG: Correo de aprobación con QR enviado. Status Code: {response_qr.status_code}")
            except Exception as e_qr:
                print(f"ERROR: No se pudo enviar el correo de aprobación con QR: {e_qr}")
        
        conn.close()
        return jsonify({
            "status": "ok",
            "message": mensaje_final,
            "qr_acceso_base64": qr_acceso_base64
        })

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"ERROR: Error de base de datos al procesar el formulario del invitado: {e}")
        return jsonify({"status": "error", "message": f"Error de base de datos al registrar datos: {e}"}), 500
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"ERROR: Error inesperado al procesar el formulario del invitado: {e}")
        return jsonify({"status": "error", "message": f"Error interno del servidor: {e}"}), 500
