import re
from unittest.mock import patch
import mongomock
import pytest
from pymongo.errors import ConnectionFailure
from app import crear_app
from mongo_config import mongo_uri
from pymongo.uri_parser import parse_uri

def test_special_characters_in_database_password():
    password = 'demo@:/?#%+ palabra'
    parsed = parse_uri(mongo_uri('mongodb://usuario@localhost:27017/blog?authSource=admin', password))
    assert parsed['password'] == password
    assert parsed['username'] == 'usuario'
    assert parsed['database'] == 'blog'
    assert parsed['options']['authSource'] == 'admin'

@pytest.fixture
def app():
    db = mongomock.MongoClient().blog
    return crear_app({'TESTING': True, 'SECRET_KEY': 'test-only-secret', 'BLOG_ADMIN_PASSWORD': 'test-only-password', 'DATABASE': db, 'SESSION_COOKIE_SECURE': False})

def token(response):
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)

def login(client):
    response = client.get('/login')
    return client.post('/login', data={'csrf_token': token(response), 'usuario': 'admin', 'password': 'test-only-password'})

def publish(client, **overrides):
    data = {'titulo': 'Entrada de prueba', 'contenido': 'Contenido de prueba', 'csrf_token': token(client.get('/'))}
    data.update(overrides)
    return client.post('/', data=data)

def test_public_read_and_author_login(app):
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert 'Agregar una entrada' not in client.get('/').text
    assert login(client).status_code == 303
    assert 'Agregar una entrada' in client.get('/').text

def test_save_redirect_refresh_and_escape(app):
    client = app.test_client(); login(client)
    assert publish(client, titulo='<script>alert(1)</script>').status_code == 303
    assert app.db.contenido.count_documents({}) == 1
    page = client.get('/')
    assert '&lt;script&gt;' in page.text and '<script>alert(1)</script>' not in page.text
    client.get('/')
    assert app.db.contenido.count_documents({}) == 1

def test_database_failure_never_reports_success(app):
    client = app.test_client(); login(client)
    with patch.object(app.db.contenido, 'insert_one', side_effect=ConnectionFailure()):
        response = publish(client)
    assert response.status_code == 503
    assert 'no se guardó' in response.text
    assert 'Publicación guardada correctamente' not in response.text
    assert app.db.contenido.count_documents({}) == 0

def test_validation(app):
    client = app.test_client(); login(client)
    for title in ['', '   ', 'x' * 151]:
        assert publish(client, titulo=title).status_code == 400
    assert publish(client, contenido=' ').status_code == 400
    assert app.db.contenido.count_documents({}) == 0

def test_csrf_and_anonymous_write(app):
    client = app.test_client()
    assert client.post('/', data={'titulo': 'No', 'contenido': 'No'}).status_code == 400
    csrf_token = token(client.get('/login'))
    assert client.post('/', data={'csrf_token': csrf_token, 'titulo': 'No', 'contenido': 'No'}).status_code == 403
    assert app.db.contenido.count_documents({}) == 0

def test_unavailable_database(app):
    app.db = None
    assert app.test_client().get('/').status_code == 503
    assert app.test_client().get('/health').status_code == 503

def test_logout_and_bad_login(app):
    client = app.test_client()
    assert client.post('/login', data={'csrf_token': token(client.get('/login')), 'usuario': 'admin', 'password': 'wrong'}).status_code == 401
    login(client)
    assert client.post('/logout', data={'csrf_token': token(client.get('/'))}).status_code == 303
    assert 'Agregar una entrada' not in client.get('/').text

