#!/usr/bin/env python
"""
Script to create a Django superuser for accessing the admin panel.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if admin user already exists
if User.objects.filter(username='admin').exists():
    print("Admin user already exists!")
    print("\nUsername: admin")
    print("Password: (the one you set)")
else:
    # Create superuser
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'  # Change this to a secure password

    User.objects.create_superuser(username=username, email=email, password=password)

    print("SUCCESS: Superuser created successfully!")
    print("\n" + "="*50)
    print("Django Admin Credentials:")
    print("="*50)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email:    {email}")
    print("="*50)
    print("\nIMPORTANT: Change the password after first login!")

print("\nAccess the admin panel at:")
print("   http://localhost:8001/django-admin/")
print("\nMake sure the server is running:")
print("   python manage.py runserver 8001")
