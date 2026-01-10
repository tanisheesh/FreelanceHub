"""
WSGI entry point for production deployment
"""
import os
from app.app import create_app
from app.models import db, User

# Create the Flask application
app = create_app('production')

# Initialize database on startup
with app.app_context():
    try:
        # Check if tables exist by trying to query
        User.query.count()
        print("✅ Database tables exist")
    except Exception as e:
        print(f"❌ Database issue: {e}")
        print("🔧 Creating database tables...")
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='tanishpoddar.18@gmail.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='tanishpoddar.18@gmail.com',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
        
        print("✅ Database initialized successfully!")

if __name__ == "__main__":
    app.run()