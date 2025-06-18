from flask import Flask, render_template
from scripts.validacion_usuarios import validacion_usuarios
from scripts.partials_admin import * #dejar solo modulos importantes
from scripts.partials_prop import *
from scripts.partials_segu import *
from scripts.perfil import perfil_bp
from scripts.invitaciones import procesar_formulario_invitado
import sqlite3
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

# --- INICIO DE LA APLICACIÓN (DEBE SER LO ÚLTIMO) ---
if __name__=='__main__': #si estamos en el main lanzamos la app
    app.run(debug=True) #activa modo debug 

    

 