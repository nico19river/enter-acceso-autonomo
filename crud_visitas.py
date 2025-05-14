from flask import Blueprint, render_template, request, redirect
import sqlite3
import os

#TODO agregar un espacio en el formulario para cargar imagen de cedula

#crea un blueprint, luego se agrega el blueprint a app.py
#de esta manera todos podemos desarrollar una parte

crud_visitas = Blueprint('crud_visitas', __name__) 

#TODO sacar la funcion de inicializar la base de datos y ponerla en un Script para inicilizar todos las tablas
def inicializar_db():
    if not os.path.exists('visitas.db'):
        conexion = sqlite3.connect('visitas.db')
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE visitas (
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
        """)
        conexion.commit()
        conexion.close()

inicializar_db()

@crud_visitas.route("/formulario")
def formulario():
    return render_template("formulario.html")  

@crud_visitas.route("/registrar_visita", methods=["POST"])
def registrar_visita():
    datos = (
        request.form['nombre'],
        request.form['dni'],
        request.form['propietario'],
        request.form['motivo'],
        request.form.get('marca', ''),
        request.form.get('modelo', ''),
        request.form.get('color', ''),
        request.form.get('patente', ''),
        request.form['fecha_ingreso'],
        request.form.get('hora_ingreso', ''),
        request.form.get('hora_salida', '')
     )

#TODO se podria mejorar la conexion con la base de datos, ponerla dentro de un metodo
#incluso ponerla en un script con todos los metodos de manejo de bases de datos
#de esta manera no repetiriamos codigo 

    conexion = sqlite3.connect('visitas.db')
    cursor = conexion.cursor()
    print("Datos a insertar:", datos)
    cursor.execute("""
        INSERT INTO visitas (nombre, dni, propietario, motivo, marca, modelo, color, patente, fecha_ingreso, hora_ingreso, hora_salida)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, datos)
    conexion.commit()
    conexion.close()

    return redirect("/confirmacion")

@crud_visitas.route("/confirmacion")
def confirmacion():
    return render_template("confirmacion.html")

@crud_visitas.route("/listar_visitas")
def listar_visitas():
    conexion = sqlite3.connect('visitas.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, dni, propietario, motivo, marca, modelo, color, patente, fecha_ingreso, hora_salida, hora_ingreso FROM visitas ORDER BY fecha_ingreso DESC, id DESC")
    visitas = cursor.fetchall()
    conexion.close()
    return render_template("listar_visitas.html", visitas=visitas)

