from flask import Flask, render_template
from crud_visitas import crud_visitas

app = Flask(__name__)

app.register_blueprint(crud_visitas, url_prefix='/visitas')

@app.route ('/')
def home():
    return render_template('index.html')
    

@app.route ('/login')
def login():
    return render_template('login.html')


if __name__=='__main__': #si estamos en el main lanzamos la app
    app.run(debug=True) #activa modo debug


    

