from flask import Blueprint, render_template, session, abort

partials_segu = Blueprint('partials_segu', __name__, template_folder='templates')

# Decorador para verificar rol seguridad
def rol_segu(f):
    def wrapper(*args, **kwargs): #args y kwargs guardan n cantidad de valores
        if session.get('user_type') != 'seguridad': #session guarda datos de usuario
            abort(403)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@partials_segu.route('/escanear-QR-acceso')
@rol_segu
def escanear_qr():
    return render_template('/partials/escanear-QR-acceso.html')

@partials_segu.route('/registrar-acceso-manual')
@rol_segu
def registar_acceso():
    return render_template('partials/registrar-acceso-manual.html')