#!/usr/bin/env python
"""Reset admin password"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_health.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Reset password for existing admin
username = 'reshmasc'
new_password = 'admin123'  # New temporary password

try:
    user = User.objects.get(username=username, is_superuser=True)
    user.set_password(new_password)
    user.save()
    
    print("\n" + "="*60)
    print("PASSWORD RESET SUCCESSFUL!")
    print("="*60)
    print(f"Username: {username}")
    print(f"New Password: {new_password}")
    print(f"Email: {user.email}")
    print("\nYou can now login at: http://127.0.0.1:8000/admin/")
    print("="*60)
    
except User.DoesNotExist:
    print(f"User '{username}' not found!")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

