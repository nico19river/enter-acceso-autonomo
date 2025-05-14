import sqlite3

conexion = sqlite3.connect('visitas.db')
cursor = conexion.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS visitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    dni TEXT NOT NULL,
    fecha_ingreso TEXT NOT NULL,
    hora_ingreso TEXT NOT NULL,
    hora_salida TEXT NOT NULL,
    patente TEXT,
    marca TEXT,
    modelo TEXT,
    color TEXT,
    propietario TEXT NOT NULL,
    motivo TEXT NOT NULL
)
''')

conexion.commit()
conexion.close()

print("Base de datos y tabla creada correctamente.")
