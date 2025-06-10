import sqlite3

def crear_base_desde_archivo(ruta_sql, ruta_db):
    with open(ruta_sql, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    print("Contenido del archivo SQL:\n", sql_script[:100])  # muestra primeros 100 caracteres para chequear que funcione
    
    conn = sqlite3.connect(ruta_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    with open(ruta_sql, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

#para que se ejecute directamente desde aca y no desde app.py
if __name__ == "__main__":
    ruta_sql = r"enter_db.sql" # estructura
    ruta_db = r"enter_local_db.db" # nombre de la base de datos
    crear_base_desde_archivo(ruta_sql, ruta_db)