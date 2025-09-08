import os
import datetime
import locale
from flask import Flask, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv

def crear_app():
    load_dotenv()
    app = Flask(__name__)

    # Conexión a MongoDB
    try:
        cliente = MongoClient(os.getenv("MONGODB_URI"))
        app.db = cliente.blog
        cliente.admin.command("ping")
        print("✅ Conectado a MongoDB")
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB: {e}")
        app.db = None

    # Establecer idioma para fechas
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/macOS
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows
        except:
            print("⚠️ No se pudo establecer el idioma español para las fechas.")

    @app.route("/", methods=["GET", "POST"])
    def home():
        entradas = []

        # ✔️ Comparar con None correctamente
        if app.db is not None:
            entradas = [entrada for entrada in app.db.contenido.find({})]

        if request.method == "POST":
            titulo = request.form.get("titulo")
            contenido_entrante = request.form.get("contenido")
            fecha_formato = datetime.datetime.today().strftime("%d de %B de %Y")

            nueva_entrada = {
                "titulo": titulo,
                "contenido": contenido_entrante,
                "fecha": fecha_formato
            }

            entradas.append(nueva_entrada)

            if app.db is not None:
                app.db.contenido.insert_one(nueva_entrada)

        return render_template("index.html", entradas=entradas)

    return app


if __name__ == "__main__":
    app = crear_app()
    app.run(debug=True)
