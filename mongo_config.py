from urllib.parse import urlsplit, urlunsplit, quote, unquote

def mongo_uri(uri, password=None):
    if not password or not uri:
        return uri
    parts = urlsplit(uri)
    if not parts.username:
        raise RuntimeError('Incluye el usuario MongoDB en MONGODB_URI')
    host = parts.netloc.rsplit('@', 1)[-1]
    user = quote(unquote(parts.username), safe='')
    netloc = f'{user}:{quote(password, safe="")}@{host}'
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

