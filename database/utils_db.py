import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---

# Este método construye una ruta al archivo de la base de datos que funcionará
# sin importar desde dónde se ejecute la aplicación, evitando errores comunes.
_dir_actual = os.path.dirname(__file__)
# Asegúrate de que este nombre coincida con tu archivo de base de datos.
DB_FILENAME = 'enter_local_db.db' 
DATABASE_PATH = os.path.join(_dir_actual, DB_FILENAME)


# --- FUNCIÓN DE CONEXIÓN ---

def get_db_connection():
    """Crea y retorna una conexión a la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error crítico al conectar con la base de datos en '{DATABASE_PATH}': {e}")
        return None

# --- FUNCIONES DE CREACIÓN (CRUD: Create) ---

def add_barrio(nombre):
    """Agrega un nuevo barrio a la base de datos."""
    sql = "INSERT INTO barrios (nombre) VALUES (?)"
    conn = get_db_connection()
    if not conn: return None, "Error de conexión."
        
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (nombre,))
        conn.commit()
        print(f"Barrio '{nombre}' agregado con éxito.")
        return cursor.lastrowid, None # Devuelve el ID y ningún error.
    except sqlite3.IntegrityError:
        return None, f"Error: El barrio '{nombre}' ya existe."
    except sqlite3.Error as e:
        return None, f"Error de base de datos al agregar barrio: {e}"
    finally:
        if conn:
            conn.close()

def add_lote(numero_lote, id_barrio):
    """Agrega un nuevo lote a un barrio específico."""
    sql = "INSERT INTO lotes (numero_lote, id_barrio) VALUES (?, ?)"
    conn = get_db_connection()
    if not conn: return None, "Error de conexión."
        
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (numero_lote, id_barrio))
        conn.commit()
        print(f"Lote '{numero_lote}' agregado al barrio {id_barrio} con éxito.")
        return cursor.lastrowid, None
    except sqlite3.Error as e:
        return None, f"Error al agregar lote: {e}"
    finally:
        if conn:
            conn.close()

def add_usuario(nombre, apellido, email, password, rol_usuario, id_barrio, pin_acceso=None, pin_seguridad=None):
    """Agrega un nuevo usuario a la base de datos, hasheando la contraseña."""
    # ¡MEJORA DE SEGURIDAD! Hasheamos la contraseña antes de guardarla.
    password_hash = generate_password_hash(password)
    
    sql = """
        INSERT INTO usuarios (nombre, apellido, email, password, rol_usuario, id_barrio, pin_acceso, pin_seguridad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn = get_db_connection()
    if not conn: return None, "Error de conexión."
        
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (nombre, apellido, email, password_hash, rol_usuario, id_barrio, pin_acceso, pin_seguridad))
        nuevo_id_usuario = cursor.lastrowid
        conn.commit()
        print(f"Usuario '{nombre} {apellido}' agregado con ID: {nuevo_id_usuario}.")
        return nuevo_id_usuario, None
    except sqlite3.IntegrityError:
        return None, f"Error: El email '{email}' ya está registrado."
    except sqlite3.Error as e:
        return None, f"Error de base de datos al agregar usuario: {e}"
    finally:
        if conn:
            conn.close()

def link_usuario_lote(id_usuario, id_lote):
    """Vincula un usuario a un lote en la tabla intermedia."""
    sql = "INSERT INTO usuarios_lotes (id_usuario, id_lote) VALUES (?, ?)"
    conn = get_db_connection()
    if not conn: return False, "Error de conexión."

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (id_usuario, id_lote))
        conn.commit()
        print(f"Usuario {id_usuario} vinculado al lote {id_lote} con éxito.")
        return True, None
    except sqlite3.IntegrityError:
        return False, f"Error: El usuario {id_usuario} ya está vinculado al lote {id_lote}."
    except sqlite3.Error as e:
        return False, f"Error al vincular usuario a lote: {e}"
    finally:
        if conn:
            conn.close()

def obtener_lotes():
    conn = get_db_connection()
    if not conn:
        print("Sin conexión")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_lote, numero_lote, id_barrio FROM lotes")
        lotes = cursor.fetchall()
        print("Lotes encontrados:", lotes)
        return lotes
    except sqlite3.Error as e:
        print(f"Error al obtener lotes: {e}")
        return []
    finally:
        conn.close()

def obtener_todos_usuarios():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre, apellido, email, rol_usuario FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def obtener_usuarios_por_rol(rol):
    if rol not in ['admin', 'propietario', 'seguridad']:
        return []
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre, apellido, email, rol_usuario FROM usuarios WHERE rol_usuario = ?", (rol,))
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios