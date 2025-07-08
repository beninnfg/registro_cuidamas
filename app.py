from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import datetime
import segno

app = Flask(__name__)
app.secret_key = 'cuida_mas_secret_key'

DATA_DIR = "datos"
QR_DIR = "static/qr"
FOTO_DIR = "static/fotos"
USERS_FILE = "datos/usuarios.json"

# Crear carpetas si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)
os.makedirs(FOTO_DIR, exist_ok=True)

@app.route('/')
def index():
    usuario = session.get('usuario')
    clinicas = [
        {"nombre": "Clínica San Pablo", "logo": "san pablo.png"},
        {"nombre": "Clínica Vida", "logo": "cvida.png"},
        {"nombre": "Clínica Ricardo Palma", "logo": "ricardo palma.png"},
        {"nombre": "VIVENCIAS Casa de Reposo", "logo": "casa aulto mayor.png"},
        {"nombre": "El hogar de mis amigos", "logo": "el hogar de mis amigos.png"}
    ]
    return render_template('index.html', usuario=usuario, clinicas=clinicas)

@app.route('/registro-centro', methods=['GET', 'POST'])
def registro_centro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        confirmar = request.form['confirmar']

        if password != confirmar:
            return render_template("registro_centro.html", error="Las contraseñas no coinciden.")

        usuarios = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)

        if any(u['correo'] == correo for u in usuarios):
            return render_template("registro_centro.html", error="Este correo ya está registrado.")

        usuarios.append({
            "nombre": nombre,
            "correo": correo,
            "password": password
        })

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=4)

        return redirect(url_for('login'))

    return render_template("registro_centro.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        if not os.path.exists(USERS_FILE):
            return render_template("login.html", error="No hay usuarios registrados.")

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            usuarios = json.load(f)

        for u in usuarios:
            if u['correo'] == correo:
                if u['password'] == password:
                    session['usuario'] = u['nombre']
                    return redirect(url_for('registro'))
                else:
                    return render_template("login.html", error="Contraseña incorrecta.")

        return render_template("login.html", error="El correo no está registrado.")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        edad = int(request.form['edad'])
        if edad < 50:
            return "Solo se permiten pacientes de 50 años a más.", 400

        datos = {
            'nombre': request.form['nombre'],
            'direccion': request.form['direccion'],
            'edad': edad,
            'sangre': request.form['sangre'],
            'alergias': request.form['alergias'],
            'emergencia': request.form['emergencia'],
            'clinica': request.form['clinica'],
            'discapacidad': request.form['discapacidad'],
            'tratamiento': request.form['tratamiento'],
            'enfermedades': request.form['enfermedades']
        }

        # Procesar foto
        foto = request.files['foto']
        if foto and foto.filename:
            foto_path = os.path.join(FOTO_DIR, foto.filename)
            foto.save(foto_path)
            datos['foto'] = foto.filename
        else:
            datos['foto'] = ""

        # Guardar JSON
        id_unico = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        json_path = os.path.join(DATA_DIR, f"{id_unico}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)

        # Generar QR
        qr_url = url_for('ver_paciente', id=id_unico, _external=True)
        qr = segno.make(qr_url)
        qr_path = os.path.join(QR_DIR, f"{id_unico}.png")
        qr.save(qr_path, scale=5)

        return render_template("resultado.html", datos=datos, qr_path="/" + qr_path.replace("\\", "/"))

    return render_template('registro.html')

@app.route('/paciente/<id>')
def ver_paciente(id):
    archivo_json = os.path.join(DATA_DIR, f"{id}.json")
    if not os.path.exists(archivo_json):
        return "Paciente no encontrado", 404

    with open(archivo_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    return render_template("paciente.html", datos=datos)

if __name__ == '__main__':
    app.run(debug=True)
