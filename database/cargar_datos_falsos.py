import sqlite3
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

def cargar_datos(ruta_db):
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()

    # Activar FK para SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    fake = Faker('es_ES')

    # Insertar un barrio
    cursor.execute("INSERT INTO barrios (nombre) VALUES (?)", ("Barrio Test",))
    id_barrio = cursor.lastrowid

    # Insertar 10 lotes para ese barrio
    lotes_ids = []
    for i in range(1, 11):
        cursor.execute("INSERT INTO lotes (numero_lote, id_barrio) VALUES (?, ?)", (f"Lote-{i}", id_barrio))
        lotes_ids.append(cursor.lastrowid)

    # Insertar 1 admin
    cursor.execute("""
        INSERT INTO usuarios (nombre, apellido, email, password, rol_usuario, id_barrio)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Admin", "Principal", "admin@barrio.test", "admin123", "admin", id_barrio))
    admin_id = cursor.lastrowid

    # Insertar 5 seguridad
    seguridad_ids = []
    for _ in range(5):
        nombre = fake.first_name()
        apellido = fake.last_name()
        email = fake.unique.email()
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password, rol_usuario, id_barrio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, email, "seg123", "seguridad", id_barrio))
        seguridad_ids.append(cursor.lastrowid)

    # Insertar 23 propietarios
    propietarios_ids = []
    for _ in range(23):
        nombre = fake.first_name()
        apellido = fake.last_name()
        email = fake.unique.email()
        pin_acceso = str(fake.random_int(min=1000, max=9999))
        pin_seguridad = str(fake.random_int(min=1000, max=9999))
        password = "prop123"

        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password, rol_usuario, id_barrio,
                pin_acceso, pin_seguridad, bloqueado, intentos_fallidos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, email, password,
              "propietario", id_barrio,
              pin_acceso, pin_seguridad, 0, 0))

        id_usuario = cursor.lastrowid
        propietarios_ids.append(id_usuario)

        # Asignar a uno o varios lotes al azar (al menos uno)
        lotes_asignados = random.sample(lotes_ids, random.randint(1, 3))
        for lote_id in lotes_asignados:
            cursor.execute("INSERT INTO usuarios_lotes (id_usuario, id_lote) VALUES (?, ?)", (id_usuario, lote_id))

        # Opcional: Insertar algunos vehículos para el propietario (0 a 2)
        cantidad_vehiculos = random.randint(0, 2)
        for _ in range(cantidad_vehiculos):
            marca = fake.company()
            modelo = fake.word().capitalize()
            color = fake.color_name()
            patente = fake.unique.license_plate()
            cursor.execute("""
                INSERT INTO vehiculos (id_usuario, marca, modelo, color, patente)
                VALUES (?, ?, ?, ?, ?)
            """, (id_usuario, marca, modelo, color, patente))

    # Crear 8 invitaciones aleatorias, invitadas por propietarios
    invitaciones_ids = []
    for _ in range(8):
        id_usuario = random.choice(propietarios_ids)
        nombre_visitante = fake.first_name()
        dni_visitante = str(fake.random_number(digits=8, fix_len=True))
        fecha_visita = (datetime.now() - timedelta(days=random.randint(0, 6))).strftime("%Y-%m-%d")
        estado = random.choice(['noAprobada', 'aprobada', 'ingresado', 'visitaconcluida'])
        token = str(uuid.uuid4())  # Token único para la invitación
        comentario = None
        vehiculo = random.choice([0, 1])  # 0: no, 1: sí
        patente = fake.license_plate() if vehiculo == 1 else None
        imagen_poliza = None
        acompanantes_mayores = ",".join([str(fake.random_number(digits=8, fix_len=True)) for _ in range(random.randint(0,2))]) or None
        acompanantes_menores = ",".join([fake.name() for _ in range(random.randint(0,2))]) or None

        cursor.execute("""
            INSERT INTO invitaciones 
            (id_usuario, nombre_visitante, dni_visitante, fecha_visita, estado, token, comentario, vehiculo, patente, imagen_poliza, acompanantes_mayores, acompanantes_menores)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_usuario, nombre_visitante, dni_visitante, fecha_visita, estado, token, comentario, vehiculo, patente, imagen_poliza, acompanantes_mayores, acompanantes_menores))
        invitaciones_ids.append(cursor.lastrowid)

    # Crear entre 12 y 14 accesos
    cantidad_accesos = random.randint(12, 14)
    for i in range(cantidad_accesos):
        # Para 8 accesos usar invitación (aleatoria de las creadas)
        if i < 8:
            id_invitacion = invitaciones_ids[i]
            cursor.execute("SELECT dni_visitante FROM invitaciones WHERE id_invitacion = ?", (id_invitacion,))
            dni_visitante = cursor.fetchone()[0]
        else:
            id_invitacion = None
            dni_visitante = str(fake.random_number(digits=8, fix_len=True))

        id_guardia = random.choice(seguridad_ids)

        ingreso_dt = datetime.now() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        salida_dt = ingreso_dt + timedelta(hours=random.randint(1, 5))
        fecha_hora_ingreso = ingreso_dt.strftime("%Y-%m-%d %H:%M:%S")
        fecha_hora_salida = salida_dt.strftime("%Y-%m-%d %H:%M:%S")
        estado = random.choice(['noAprobado', 'enCurso', 'finalizado'])
        token_qr = "manual"

        cantidad_acompañantes = random.randint(0, 3)
        dni_acompañantes = ",".join([str(fake.random_number(digits=8, fix_len=True)) for _ in range(cantidad_acompañantes)]) if cantidad_acompañantes > 0 else None
        hay_acompañante_menor = random.choice([0, 1]) if cantidad_acompañantes > 0 else 0

        patente = fake.license_plate() if random.random() > 0.5 else None

        cursor.execute("""
            INSERT INTO accesos (
                id_invitacion, id_guardia, fecha_hora_ingreso, fecha_hora_salida, estado,
                token_qr, dni_visitante, dni_acompañantes, cantidad_acompañantes, hay_acompañante_menor, patente
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_invitacion, id_guardia, fecha_hora_ingreso, fecha_hora_salida, estado,
            token_qr, dni_visitante, dni_acompañantes, cantidad_acompañantes, hay_acompañante_menor, patente
        ))

    conn.commit()
    conn.close()
    print("Datos de prueba cargados con éxito.")

if __name__ == "__main__":
    ruta_db = r"enter_DATABASE.db"
    cargar_datos(ruta_db)
