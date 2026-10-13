import os
import hmac
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from mongo_config import mongo_uri

csrf = CSRFProtect()

def crear_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        MONGODB_URI=os.getenv("MONGODB_URI"),
        MONGODB_PASSWORD=os.getenv("MONGODB_PASSWORD"),
        MONGODB_DATABASE=os.getenv("MONGODB_DATABASE", "blog"),
        BLOG_ADMIN_USER=os.getenv("BLOG_ADMIN_USER", "admin"),
        BLOG_ADMIN_PASSWORD=os.getenv("BLOG_ADMIN_PASSWORD"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "true").lower() == "true",
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("Configura SECRET_KEY antes de iniciar el blog.")
    csrf.init_app(app)
    app.db = None
    if app.config.get("DATABASE") is not None:
        app.db = app.config["DATABASE"]
    elif app.config["MONGODB_URI"]:
        client = MongoClient(mongo_uri(app.config["MONGODB_URI"], app.config["MONGODB_PASSWORD"]), serverSelectionTimeoutMS=5000)
        app.extensions["mongo_client"] = client
        app.db = client[app.config["MONGODB_DATABASE"]]

    @app.template_filter("fecha_es")
    def fecha_es(value):
        if not isinstance(value, datetime):
            return value or ""
        value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        value = value.astimezone(timezone(timedelta(hours=-4)))
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{value.day} de {meses[value.month - 1]} de {value.year}"

    def render_home(status=200, error=None):
        entradas = []
        try:
            if app.db is None:
                raise PyMongoError("Database unavailable")
            entradas = list(app.db.contenido.find({}).sort("_id", -1).limit(100))
        except PyMongoError:
            app.logger.warning("No se pudo consultar MongoDB.")
            status, error = 503, "El blog no está disponible temporalmente. Inténtalo de nuevo."
        return render_template("index.html", entradas=entradas, error=error,
                               form_data=request.form), status

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "GET":
            return render_home()
        if not session.get("admin"):
            return render_home(403, "Inicia sesión para publicar.")
        titulo = request.form.get("titulo", "").strip()
        contenido = request.form.get("contenido", "").strip()
        if not titulo or not contenido or len(titulo) > 150 or len(contenido) > 10000:
            return render_home(400, "Escribe un título de hasta 150 caracteres y contenido de hasta 10 000.")
        try:
            if app.db is None:
                raise PyMongoError("Database unavailable")
            app.db.contenido.insert_one({"titulo": titulo, "contenido": contenido,
                                        "fecha": datetime.now(timezone.utc)})
        except PyMongoError:
            app.logger.warning("No se pudo guardar la publicación.")
            return render_home(503, "La publicación no se guardó. Inténtalo de nuevo.")
        flash("Publicación guardada correctamente.")
        return redirect(url_for("home"), code=303)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            user = request.form.get("usuario", "")
            password = request.form.get("password", "")
            expected = app.config["BLOG_ADMIN_PASSWORD"]
            if expected and hmac.compare_digest(user.encode(), app.config["BLOG_ADMIN_USER"].encode()) and hmac.compare_digest(password.encode(), expected.encode()):
                session.clear()
                session["admin"] = True
                return redirect(url_for("home"), code=303)
            error = "No se pudo iniciar sesión."
        return render_template("login.html", error=error), (401 if error else 200)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"), code=303)

    @app.get("/health")
    def health():
        try:
            if app.db is None:
                raise PyMongoError("Database unavailable")
            app.db.command("ping")
        except PyMongoError:
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok"), 200

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("error.html", message="El formulario caducó. Vuelve a abrir la página e inténtalo de nuevo."), 400

    @app.errorhandler(413)
    def too_large(error):
        return render_template("error.html", message="El contenido enviado es demasiado grande."), 413

    return app

if __name__ == "__main__":
    crear_app().run(host="127.0.0.1", debug=False)

