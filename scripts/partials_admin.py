from flask import Blueprint, render_template, session, abort

partials_admin = Blueprint('partials_admin', __name__, template_folder='templates')

# Decorador para verificar rol admin 
def rol_admin(f):
    def wrapper(*args, **kwargs): #args y kwargs guardan n cantidad de valores
        if session.get('user_type') != 'admin': #session guarda datos de usuario
            abort(403)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@partials_admin.route('/crear-usuario')
@rol_admin
def crear_usuario():
    return render_template('partials/crear_usuario.html')

@partials_admin.route('/borrar-usuario')
@rol_admin
def borrar_usuario():
    return render_template('partials/borrar_usuario.html')

@partials_admin.route('/listar-usuarios')
@rol_admin
def listar_usuarios():
    return render_template('partials/listar_usuarios.html')