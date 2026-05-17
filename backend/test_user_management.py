#!/usr/bin/env python
"""
Simple test script to verify user management endpoints.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atomquest.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from portal.models import UserProfile, Department, AuditLog

def test_user_management():
    """Test user management endpoints."""
    print("Starting user management tests...")
    
    # Create test data
    dept = Department.objects.create(name='Sales')
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(user=admin_user, role='admin')
    
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    # Test 1: List users
    print("\n1. Testing list users...")
    response = client.get('/api/user-management/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("   ✓ List users passed")
    
    # Test 2: Create user
    print("\n2. Testing create user...")
    data = {
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'testpass123',
        'role': 'employee',
        'department_id': dept.id
    }
    response = client.post('/api/user-management/', data)
    print(f"   Status: {response.status_code}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    print("   ✓ Create user passed")
    
    # Test 3: Retrieve user
    print("\n3. Testing retrieve user...")
    new_user = User.objects.get(username='newuser')
    response = client.get(f'/api/user-management/{new_user.id}/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("   ✓ Retrieve user passed")
    
    # Test 4: Update user role
    print("\n4. Testing update user role...")
    data = {'role': 'manager'}
    response = client.put(f'/api/user-management/{new_user.id}/', data)
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    new_user.profile.refresh_from_db()
    assert new_user.profile.role == 'manager', f"Expected role 'manager', got {new_user.profile.role}"
    print("   ✓ Update user role passed")
    
    # Test 5: Deactivate user
    print("\n5. Testing deactivate user...")
    response = client.post(f'/api/user-management/{new_user.id}/deactivate/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    new_user.profile.refresh_from_db()
    assert not new_user.profile.is_active, "Expected user to be inactive"
    print("   ✓ Deactivate user passed")
    
    # Test 6: Reactivate user
    print("\n6. Testing reactivate user...")
    response = client.post(f'/api/user-management/{new_user.id}/reactivate/')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    new_user.profile.refresh_from_db()
    assert new_user.profile.is_active, "Expected user to be active"
    print("   ✓ Reactivate user passed")
    
    # Test 7: Audit trail
    print("\n7. Testing audit trail...")
    audit_logs = AuditLog.objects.filter(entity_type='user', entity_id=new_user.id)
    print(f"   Audit logs count: {audit_logs.count()}")
    assert audit_logs.count() > 0, "Expected audit logs to be created"
    print("   ✓ Audit trail passed")
    
    print("\n✓ All tests passed!")

if __name__ == '__main__':
    test_user_management()
