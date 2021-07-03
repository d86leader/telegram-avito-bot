def check_avito_url(avito_url):
    from urllib.parse import urlparse
    url_parts = urlparse(avito_url)
    return url_parts.netloc == 'm.avito.ru' and len(url_parts.path) > 1
