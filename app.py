from flask import Flask, render_template
from crud_visitas import crud_visitas
from scripts.validacion_usuarios import validacion_usuarios

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta_1234567890' #



app.register_blueprint(crud_visitas, url_prefix='/visitas')
app.register_blueprint(validacion_usuarios)

@app.route('/')
def home():
    return render_template('home.html')
    

@app.route ('/login')
def login():
    return render_template('login.html')


if __name__=='__main__': #si estamos en el main lanzamos la app
    app.run(debug=True) #activa modo debug


    

