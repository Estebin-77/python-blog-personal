# Blog personal con Flask y MongoDB

Proyecto de aprendizaje con Python, Flask, Jinja, HTML, CSS y PyMongo. Las entradas son públicas; solo el autor con sesión iniciada puede publicar.

## Ejecutar localmente

1. Crea un entorno: `python -m venv .venv` y actívalo.
2. Instala: `pip install -r requirements.txt`.
3. Copia `.env.example` a `.env`. Configura `SECRET_KEY` aleatoria, `MONGODB_URI`, `BLOG_ADMIN_USER` y `BLOG_ADMIN_PASSWORD`.
4. Para HTTP local utiliza `COOKIE_SECURE=false`; en producción `true`.
5. Ejecuta `flask --app app:crear_app run`.

`python seed.py` carga dos publicaciones de muestra sin reemplazar las existentes. La lectura muestra hasta 100 entradas recientes. Se conserva compatibilidad con las fechas de texto de las entradas antiguas.

## Comportamiento y seguridad

- Validación de título y contenido en el servidor.
- Protección CSRF de formularios con Flask-WTF.
- Sesión del autor en una cookie firmada, HttpOnly, SameSite=Lax y Secure en producción.
- Contraseña configurada fuera del repositorio. Sin ella no se habilita el inicio de sesión.
- Confirmación de publicación solo después de que MongoDB la guarde.
- Redirección 303 después de publicar para evitar reenviar el formulario al actualizar.
- Ante fallos de MongoDB, respuesta 503 y mensaje visible; no se simula un guardado correcto.
- El contenido se muestra escapado mediante Jinja.

Este acceso de un único autor es una solución sencilla de portafolio, no un sistema completo de usuarios. No incluye recuperación de contraseña ni limitación de intentos de inicio de sesión.

## Pruebas

`pip install -r requirements-dev.txt` y `python -m pytest -q`.
Las pruebas usan mongomock y fallos simulados: no modifican datos reales. Verifica también `/health` y una publicación de prueba en el despliegue para comprobar la conexión real.

## Render

Build: `pip install -r requirements.txt`. Inicio: `gunicorn 'app:crear_app()'`. Health: `/health`.
Variables: `MONGODB_URI`, `MONGODB_DATABASE=blog`, `SECRET_KEY`, `BLOG_ADMIN_USER`, `BLOG_ADMIN_PASSWORD`, `COOKIE_SECURE=true`.
Para cargar datos de muestra, añade temporalmente `&& python seed.py` al build y después retíralo.

## Para explicar en una entrevista

Flask recibe la petición, PyMongo accede a los documentos de MongoDB y Jinja genera HTML. Los formularios usan POST; Flask-WTF valida el token CSRF. La sesión distingue al autor de los lectores. La aplicación se organiza mediante una función crear_app, lo que facilita configurar el servidor y las pruebas. No utiliza Django, React ni SQLite.
