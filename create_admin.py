#!/usr/bin/env python
"""Create or reset admin superuser"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_health.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123'  # Change this after first login!

def create_admin():
    """Create or update admin superuser"""
    try:
        # Check if admin user exists
        user, created = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={
                'email': ADMIN_EMAIL,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'role': 'doctor'  # Admin can be doctor role
            }
        )
        
        if not created:
            # Update existing user
            user.email = ADMIN_EMAIL
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            print(f"Updating existing user: {ADMIN_USERNAME}")
        else:
            print(f"Creating new admin user: {ADMIN_USERNAME}")
        
        # Set password
        user.set_password(ADMIN_PASSWORD)
        user.save()
        
        print("\n" + "="*60)
        print("ADMIN CREDENTIALS CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Password: {ADMIN_PASSWORD}")
        print(f"Email: {ADMIN_EMAIL}")
        print("\nYou can now login at: http://127.0.0.1:8000/admin/")
        print("="*60)
        print("\n⚠️  WARNING: Change the password after first login!")
        print("="*60)
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin()

