#!/usr/bin/env python3
"""
Database initialization script for FreelanceHub
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import create_app
    from app.models import db, User, Portfolio
except ImportError:
    from app.app import create_app
    from app.models import db, User, Portfolio

def init_database():
    """Initialize the database and create tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if admin user exists
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@freelancehub.com')
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email=admin_email,
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_active=True
            )
            # Use environment variable for admin password or default
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print("   ⚠️  Please change this password after first login!")
        else:
            print("✅ Admin user already exists!")
        
        # Create a sample portfolio for testing
        sample_portfolio = Portfolio.query.filter_by(user_id=admin.id).first()
        if not sample_portfolio:
            print("Creating sample portfolio...")
            sample_portfolio = Portfolio(
                user_id=admin.id,
                title="Admin's Portfolio",
                bio="Welcome to my portfolio! I'm a passionate freelancer with expertise in various technologies.",
                is_public=True,
                is_approved=True,
                is_featured=True
            )
            db.session.add(sample_portfolio)
            db.session.commit()
            print("✅ Sample portfolio created successfully!")
        else:
            print("✅ Sample portfolio already exists!")
        
        print("\n🎉 Database initialization completed!")
        print("You can now run the application with: python app/app.py")

if __name__ == '__main__':
    init_database() 