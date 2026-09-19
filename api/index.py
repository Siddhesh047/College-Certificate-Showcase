import os
import sys

# Ensure project root is in Python sys.path so app, models, etc. can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import app

class VercelPathFix:
    """
    WSGI middleware to fix PATH_INFO on Vercel serverless deployments.
    Vercel rewrites set PATH_INFO to '/api/index.py' (or '/api'), which causes
    Flask to return a 404 Not Found error because no route matches '/api/index.py'.
    This middleware restores PATH_INFO from HTTP_X_MATCHED_PATH, HTTP_X_FORWARDED_URI,
    or strips the /api/index.py prefix.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get('HTTP_X_MATCHED_PATH') or environ.get('HTTP_X_FORWARDED_URI')
        if matched_path:
            # Strip query string if present
            if '?' in matched_path:
                matched_path = matched_path.split('?')[0]
            environ['PATH_INFO'] = matched_path
        else:
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith('/api/index.py'):
                path = path_info.replace('/api/index.py', '', 1)
                environ['PATH_INFO'] = path if path else '/'
            elif path_info.startswith('/api/index'):
                path = path_info.replace('/api/index', '', 1)
                environ['PATH_INFO'] = path if path else '/'
            elif path_info.startswith('/api'):
                path = path_info.replace('/api', '', 1)
                environ['PATH_INFO'] = path if path else '/'

        return self.wsgi_app(environ, start_response)

# Wrap Flask's WSGI app with the path fix middleware
app.wsgi_app = VercelPathFix(app.wsgi_app)
