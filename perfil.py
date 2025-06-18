from flask import Blueprint, render_template, session, redirect, url_for
from database.utils_db import obtener_datos_usuario  

perfil_bp = Blueprint('perfil_bp', __name__)

@perfil_bp.route('/perfil')
def perfil():
    print("Sesión actual:", session)
    if 'user_id' not in session:
        return redirect(url_for('home')) 

    rol = session.get('rol')
    usuario_id = session['user_id']

    # Obtener los datos del usuario
    datos = obtener_datos_usuario(usuario_id, rol)

    # Agrega un print para verificar qué datos estás obteniendo
    print("Datos del usuario:", datos)

    return render_template('perfil.html', rol=rol, datos=datos)
