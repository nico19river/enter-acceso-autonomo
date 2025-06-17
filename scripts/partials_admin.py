from flask import Blueprint, render_template, session, abort,request, redirect, flash, url_for
from database.utils_db import add_usuario, link_usuario_lote, obtener_lotes, get_db_connection

partials_admin = Blueprint('partials_admin', __name__, template_folder='templates')

# Decorador para verificar rol admin 
def rol_admin(f):
    def wrapper(*args, **kwargs): #args y kwargs guardan n cantidad de valores
        if session.get('user_type') != 'admin': #session guarda datos de usuario
            abort(403)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# CREAR USUARIO #

@partials_admin.route('/crear-usuario')
@rol_admin
def seleccionar_rol_crear_usuario():
    # Renderiza un nuevo template que crearemos.
    return render_template('partials/admin/seleccionar_rol.html')

@partials_admin.route('/crear-usuario-form/<string:rol>')
@rol_admin
def mostrar_formulario_crear_usuario(rol):
    # Validamos que el rol sea uno de los permitidos.
    roles_validos = ['admin', 'propietario', 'seguridad']
    if rol not in roles_validos:
        abort(404)  # Si no es válido, mostramos un error 404.

    lotes = obtener_lotes()  
    print(f"[DEBUG] Lotes encontrados: {[dict(l) for l in lotes]}")

    # Renderizamos una plantilla de formulario y le pasamos el rol seleccionado.
    return render_template('partials/admin/formulario_crear_usuario.html', rol_seleccionado=rol, lotes=lotes)

@partials_admin.route('/guardar-usuario', methods=['POST'])
@rol_admin
def guardar_usuario():
    # Recogemos todos los datos del formulario
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    email = request.form.get('email')
    password = request.form.get('password')
    rol_usuario = request.form.get('rol_usuario')
    id_barrio = request.form.get('id_barrio')
    
    # Recogemos los campos opcionales
    pin_acceso = request.form.get('pin_acceso')
    pin_seguridad = request.form.get('pin_seguridad')
    id_lote = request.form.get('id_lote')
    
    # Llamamos a la función para agregar el usuario
    nuevo_id, error = add_usuario(nombre, apellido, email, password, rol_usuario, id_barrio, pin_acceso, pin_seguridad)

    if error:
        # Si hubo un error al crear el usuario, lo mostramos.
        # En una app real, aquí se mostraría un template de error.
        return f"""
                <script>
                    alert("Error al crear usuario: {error}");
                    window.history.back();  
                </script>
                """

    # Si el usuario es un propietario y se seleccionó un lote, lo vinculamos.
    if rol_usuario == 'propietario' and id_lote:
        exito_link, error_link = link_usuario_lote(nuevo_id, id_lote)
        if error_link:
            # Si falla la vinculación, informamos del problema.
             return f"""
                <script>
                    alert("Usuario creado con ID {nuevo_id}, pero hubo un error al vincular el lote: {error_link}");
                    window.history.back();  
                </script>
                """

    # Si todo salió bien, redirigimos a una página de éxito (o a la lista de usuarios).
    return """
        <script>
            alert("Usuario creado con éxito.");
            window.location.href = "/dashboard-prop";  
        </script>
        """




#BORRAR USUARIO CON BUSQUEDA

@partials_admin.route('/borrar-usuario', methods=['GET', 'POST'])
@partials_admin.route('/borrar_usuario', methods=['GET', 'POST'])
@rol_admin
def borrar_usuario():
    usuarios = []
    termino = None
    if request.method == 'POST':
        termino = request.form.get('termino_busqueda')
        if termino:
            conn = get_db_connection()
            cursor = conn.cursor()
            like_term = f"%{termino}%"
            cursor.execute("""
                SELECT id_usuario, nombre, apellido, email, rol_usuario
                FROM usuarios
                WHERE id_usuario LIKE ? OR nombre LIKE ? OR apellido LIKE ? OR email LIKE ?
            """, (like_term, like_term, like_term, like_term))
            usuarios = cursor.fetchall()
            conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Devuelve solo la tabla para insertar en AJAX
        return render_template('partials/admin/tabla_borrar_usuarios.html', usuarios=usuarios)

    return render_template('partials/admin/borrar-usuario.html', usuarios=usuarios, termino=termino)

@partials_admin.route('/eliminar_usuario/<int:id_usuario>', methods=['POST'])
@partials_admin.route('/eliminar-usuario/<int:id_usuario>', methods=['POST'])
@rol_admin
def eliminar_usuario(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    conn.commit()
    conn.close()
    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for('partials_admin.borrar_usuario'))




# LISTAR USUARIOS:
@partials_admin.route('/listar-usuarios')
@rol_admin
def listar_usuarios():
    rol_filtro = request.args.get('rol')

    conn = get_db_connection()
    if not conn:
        return "Error de conexión a la base de datos", 500
    cursor = conn.cursor()

    if rol_filtro and rol_filtro in ['admin', 'propietario', 'seguridad']:
        cursor.execute("SELECT id_usuario, nombre, apellido, email, rol_usuario FROM usuarios WHERE rol_usuario = ?", (rol_filtro,))
    else:
        cursor.execute("SELECT id_usuario, nombre, apellido, email, rol_usuario FROM usuarios")

    usuarios = cursor.fetchall()
    conn.close()

    # Si es petición AJAX devolvemos solo la tabla renderizada
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/admin/tabla_usuarios.html', usuarios=usuarios)

    # Si es petición normal, renderizamos la página completa con la tabla incluida
    return render_template('partials/admin/listar-usuarios.html', usuarios=usuarios, rol_seleccionado=rol_filtro)