"""WSGI entry point for Render deployment (gunicorn compatibility)."""
import sys
import os

# Ensure parent directory is in path so we can import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2wsgi import ASGIMiddleware
from server import app

application = ASGIMiddleware(app)
