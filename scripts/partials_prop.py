from flask import Blueprint, render_template, session, abort

partials_prop = Blueprint('partials_prop', __name__, template_folder='templates')

# Decorador para verificar rol prop 
def rol_prop(f):
    def wrapper(*args, **kwargs): #args y kwargs guardan n cantidad de valores
        if session.get('user_type') != 'propietario': #session guarda datos de usuario
            abort(403)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@partials_prop.route('/enviar-invitacion')
@rol_prop
def crear_usuario():
    return render_template('partials/enviar-invitacion.html')

@partials_prop.route('/llave-virtual')
@rol_prop
def enviar_invitacion():
    return render_template('partials/llave-virtual.html')