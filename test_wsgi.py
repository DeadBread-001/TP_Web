from pprint import pformat
from urllib.parse import parse_qsl
HELLO_WORLD = "Hello world!\n"


def simple_app(environ, start_response):
    query_string = environ.get('QUERY_STRING', '')
    get_params = dict(kv.split('=') for kv in query_string.split('&') if kv)

    if environ['REQUEST_METHOD'] == 'POST':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            content_length = 0

        post_data = environ['wsgi.input'].read(content_length).decode('utf-8')
        post_params = dict(kv.split('=') for kv in post_data.split('&') if kv)
    else:
        post_params = {}

    print("GET parameters:", get_params)
    print("POST parameters:", post_params)

    response_body = HELLO_WORLD
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    start_response('200 OK', response_headers)

    return [response_body.encode('utf-8')]


application = simple_app


class AppClass:
    """Produce the same output, but using a class

    (Note: 'AppClass' is the "application" here, so calling it
    returns an instance of 'AppClass', which is then the iterable
    return value of the "application callable" as required by
    the spec.

    If we wanted to use *instances* of 'AppClass' as application
    objects instead, we would have to implement a '__call__'
    method, which would be invoked to execute the application,
    and we would need to create an instance for use by the
    server or gateway.
    """

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        self.start(status, response_headers)
        yield HELLO_WORLD
