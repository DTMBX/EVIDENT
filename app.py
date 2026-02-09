#!/usr/bin/env python
"""
Evident Platform - Main Flask Application
Complete authentication and dashboard system
"""

import os
from dotenv import load_dotenv
from app_config import create_app

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app()

# CLI Commands
@app.shell_context_processor
def make_shell_context():
    """Make shell context for Flask shell"""
    from auth.models import db, User, UserRole, TierLevel
    return {
        'db': db,
        'User': User,
        'UserRole': UserRole,
        'TierLevel': TierLevel,
    }


if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("\n" + "="*80)
    print("🚀 EVIDENT PLATFORM - STARTING")
    print("="*80)
    print(f"  Environment: {os.environ.get('FLASK_ENV', 'development').upper()}")
    print(f"  Debug Mode: {'ON' if debug else 'OFF'}")
    print(f"  Server: http://localhost:{port}")
    print()
    print("📍 Access Points:")
    print(f"  • Home: http://localhost:{port}/")
    print(f"  • Login: http://localhost:{port}/auth/login")
    print(f"  • Register: http://localhost:{port}/auth/register")
    print(f"  • Dashboard: http://localhost:{port}/dashboard")
    print(f"  • Admin: http://localhost:{port}/admin/")
    print()
    print("🔑 Default Credentials:")
    print("  • Email: admin@Evident.info")
    print("  • Password: (create with 'flask create-admin')")
    print()
    print("⚙️  Commands:")
    print("  • flask init-db          # Initialize database")
    print("  • flask create-admin     # Create admin user")
    print("  • flask list-users       # List all users")
    print("  • flask shell            # Python shell")
    print()
    print("💡 Press Ctrl+C to stop")
    print("="*80 + "\n")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        use_reloader=debug
    )
