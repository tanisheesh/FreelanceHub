"""
WSGI entry point for production deployment
"""
import os
from app.app import create_app

# Create the Flask application
app = create_app('production')

if __name__ == "__main__":
    app.run()