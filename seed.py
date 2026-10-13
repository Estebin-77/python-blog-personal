import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from mongo_config import mongo_uri

def seed():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    if not uri:
        raise RuntimeError('Falta MONGODB_URI')
    with MongoClient(mongo_uri(uri, os.getenv('MONGODB_PASSWORD')), serverSelectionTimeoutMS=5000) as client:
        collection = client[os.getenv('MONGODB_DATABASE', 'blog')].contenido
        for title, content in [
            ('De una idea a una aplicación web', 'Aprender desarrollo web me ha llevado a conectar interfaces, servidores y bases de datos. Este blog es uno de mis proyectos de práctica con Python, Flask y MongoDB.'),
            ('Qué aprendí trabajando con formularios', 'Guardar información requiere validar los datos y comprobar que la base de datos recibió la operación. Un mensaje de éxito debe aparecer únicamente después de guardar. También incorporé protección CSRF y acceso del autor para publicar.'),
        ]:
            collection.update_one({'demo_slug': title}, {'$setOnInsert': {'demo_slug': title, 'titulo': title, 'contenido': content, 'fecha': datetime.now(timezone.utc)}}, upsert=True)
        print('Publicaciones de muestra preparadas sin modificar las existentes.')

if __name__ == '__main__':
    seed()
