#!/usr/bin/env python
"""
WSGI entry point for production deployment
Use with gunicorn or other WSGI servers
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Flask app
from app_config import create_app

# Create the WSGI application
app = create_app()

if __name__ == '__main__':
    # For local testing with WSGI server
    # Run with: gunicorn wsgi:app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
