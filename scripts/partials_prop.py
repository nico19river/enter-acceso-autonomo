from flask import Blueprint, render_template, session, abort, request, jsonify
from scripts.llave_virtual import generar_llave_virtual  # Importamos la función de lógica qr
from scripts.invitaciones import enviar_invitacion
from functools import wraps

partials_prop = Blueprint('partials_prop', __name__, template_folder='templates')

def rol_prop(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('user_type') != 'propietario':
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@partials_prop.route('/llave-virtual')
@rol_prop
def mostrar_formulario_pin():
    # Renderizamos solo el fragmento HTML con formulario y script
    return render_template('partials/propietario/formulario_pin.html')

@partials_prop.route('/generar-qr', methods=['POST'])
@rol_prop
def generar_qr():
    # Aquí delegamos la lógica de generación de QR al archivo llave_virtual.py
    return generar_llave_virtual()

@partials_prop.route('/enviar-invitacion-form') # <--- ESTA ES LA RUTA QUE NECESITAS
@rol_prop
def mostrar_formulario_invitacion():
    print("DEBUG: Accediendo a /enviar-invitacion-form. Renderizando formulario_invitacion.html")
    return render_template('partials/propietario/formulario_invitacion.html') # <--- Renderiza tu HTML

@partials_prop.route('/enviar-invitacion', methods=['POST'])
@rol_prop
def procesar_envio_invitacion():
    print("DEBUG: Petición POST recibida en /enviar-invitacion.")
    return enviar_invitacion()  