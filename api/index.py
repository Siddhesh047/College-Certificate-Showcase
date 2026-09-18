import os
import sys

# Ensure project root is in Python sys.path so app, models, etc. can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import app

# Vercel serverless function entrypoint
# The WSGI app is directly callable by Vercel's Python runtime
