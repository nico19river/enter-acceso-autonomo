from flask import Flask, render_template
from scripts.validacion_usuarios import validacion_usuarios
from scripts.partials_admin import * #dejar solo modulos importantes
from scripts.partials_prop import *
from scripts.partials_segu import *
from scripts.perfil import perfil_bp
from scripts.invitaciones import procesar_formulario_invitado
import sqlite3
from sqlite3 import Error
from datetime import datetime
from database.utils_db import get_db_connection # <-- ¡Asegúrate de esta importación para get_db_connection!

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta_1234567890' #

# --- REGISTRO DE BLUEPRINTS ---
app.register_blueprint(validacion_usuarios)
app.register_blueprint(partials_admin)
app.register_blueprint(partials_prop)
app.register_blueprint(partials_segu)
app.register_blueprint(perfil_bp)

# --- DEFINICIÓN DE RUTAS ---

@app.route('/')
def home():
    return render_template('home.html') #llama a la validacion desde home


@app.route('/invitacion/<token_invitacion>', methods=['GET'])
def mostrar_formulario_invitado(token_invitacion):
    """
    Muestra el formulario para que el invitado complete sus datos.
    Valida el token de invitación y verifica su estado y expiración.
    """
    print(f"DEBUG: Accediendo a /invitacion/{token_invitacion} (GET).")
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Buscar la invitación por el token
    cursor.execute("SELECT * FROM invitaciones WHERE token = ?", (token_invitacion,))
    invitacion = cursor.fetchone()
    conn.close()

    if not invitacion:
        print(f"ERROR: Invitación con token {token_invitacion} no encontrada.")
        return render_template('invitado/invitacion_error.html', message='Invitación no válida o ya utilizada.'), 404

    # Verificar estado de la invitación
    # 'noAprobada' es tu estado inicial.
    # Considera también si necesitas 'pendiente' si lo manejas en algún punto
    if invitacion['estado'] not in ['noAprobada', 'pendiente']:
        print(f"DEBUG: Invitación con token {token_invitacion} ya procesada o en estado no apto ({invitacion['estado']}).")
        return render_template('invitado/invitacion_error.html', message=f'Esta invitación ya ha sido {invitacion["estado"]}.'), 403

    # Verificar fecha de visita (considera la fecha actual)
    fecha_visita_db = datetime.strptime(invitacion['fecha_visita'], '%Y-%m-%d').date()
    hoy = datetime.now().date()

    if fecha_visita_db < hoy:
        print(f"DEBUG: Invitación con token {token_invitacion} ha expirado (fecha pasada).")
        return render_template('invitado/invitacion_error.html', message='Esta invitación ha caducado.'), 403

    print(f"DEBUG: Invitación válida encontrada para token {token_invitacion}.")
    # Pasamos el objeto 'invitacion' completo a la plantilla
    return render_template('invitado/formulario_datos_invitado.html', token=token_invitacion, invitacion=invitacion)


@app.route('/procesar-invitacion', methods=['POST'])
def handle_procesar_invitacion():
    print("DEBUG: Petición POST recibida en /procesar-invitacion.")
    return procesar_formulario_invitado()

@app.route('/invitacion/gracias')
def invitado_gracias():
    print("DEBUG: Accediendo a /invitacion/gracias. Renderizando gracias.html")
    return render_template('invitado/gracias.html')

@app.route('/acceso/<token_invitacion>', methods=['GET'])
def mostrar_acceso_concedido(token_invitacion):
    """
    Muestra la página de acceso concedido si el token de la INVITACIÓN es válido y el estado es 'aprobada'.
    También puede marcar la invitación como 'usada' o registrar el acceso.
    """
    print(f"DEBUG: Accediendo a /acceso/{token_invitacion} (GET).")
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Buscar la invitación por el token de INVITACIÓN original
        cursor.execute("SELECT * FROM invitaciones WHERE token = ?", (token_invitacion,))
        invitacion = cursor.fetchone()

        if not invitacion:
            print(f"ERROR: Token de acceso '{token_invitacion}' no encontrado o no válido.")
            return render_template('invitado/acceso_error.html', message='Código de acceso no válido.'), 404

        # Verificar que el estado de la invitación asociada al token sea 'aprobada'
        if invitacion['estado'] != 'aprobada':
            print(f"ERROR: Acceso con token '{token_invitacion}' denegado. Estado: {invitacion['estado']}.")
            return render_template('invitado/acceso_error.html', message=f'Acceso denegado. Estado de invitación: {invitacion["estado"]}.'), 403


        print(f"DEBUG: Acceso concedido para invitación ID: {invitacion['id_invitacion']}.")
        return render_template('invitado/acceso_concedido.html', invitacion=invitacion)

    except sqlite3.Error as e:
        print(f"ERROR: Error de base de datos al verificar token de acceso: {e}")
        return render_template('invitado/acceso_error.html', message=f"Error interno al verificar acceso: {e}"), 500
    finally:
        conn.close()

#-- PAGINA ACCESOS CONCEDIDO PARA LEER QR --
@app.route('/validar-llave/<token>', methods=['GET'])
def validar_llave_virtual_qr_simple(token): # CAMBIO: Nombre de función para diferenciar y simplificar
    print(f"DEBUG: Accediendo a /validar-llave/{token} (GET) para mostrar acceso concedido simple.")
    # No se realiza ninguna consulta a la DB ni validación del token aquí,
    # solo se muestra la página de acceso concedido.
    # Puedes pasar el token a la plantilla si quieres mostrarlo.
    return render_template('acceso_llave_virtual.html', token=token, mensaje="Acceso Concedido (Simple)") 

# --- INICIO DE LA APLICACIÓN (DEBE SER LO ÚLTIMO) ---
if __name__=='__main__': #si estamos en el main lanzamos la app
    app.run(debug=True) #activa modo debug 

    

 