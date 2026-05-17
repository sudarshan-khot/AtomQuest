"""
Management command to create 3 hardcoded test users (always available).

Run: python manage.py seed_test_users

Users created:
  admin_user  / Admin@123   — Admin role
  manager_user / Manager@123 — Manager role
  emp_user    / Employee@123 — Employee role
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portal.models import UserProfile, Department


TEST_USERS = [
    {
        'username':   'admin_user',
        'password':   'Admin@123',
        'email':      'admin@atomquest.dev',
        'first_name': 'Alice',
        'last_name':  'Admin',
        'role':       'admin',
        'dept':       'Engineering',
    },
    {
        'username':   'manager_user',
        'password':   'Manager@123',
        'email':      'manager@atomquest.dev',
        'first_name': 'Bob',
        'last_name':  'Manager',
        'role':       'manager',
        'dept':       'Sales',
    },
    {
        'username':   'emp_user',
        'password':   'Employee@123',
        'email':      'employee@atomquest.dev',
        'first_name': 'Carol',
        'last_name':  'Employee',
        'role':       'employee',
        'dept':       'Sales',
    },
]


class Command(BaseCommand):
    help = 'Create 3 hardcoded test users for role-based testing'

    def handle(self, *args, **options):
        manager_user_obj = None

        for data in TEST_USERS:
            # Get or create the Django User
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email':      data['email'],
                    'first_name': data['first_name'],
                    'last_name':  data['last_name'],
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Created user: {data['username']}"))
            else:
                # Always reset password so credentials stay predictable
                user.set_password(data['password'])
                user.save()
                self.stdout.write(f"  User exists, password reset: {data['username']}")

            # Get or create department
            dept = None
            if data.get('dept'):
                dept, _ = Department.objects.get_or_create(
                    name=data['dept'],
                    defaults={'description': data['dept']}
                )

            # Get or create UserProfile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role':       data['role'],
                    'department': dept,
                    'is_active':  True,
                }
            )
            # Always sync role and department in case they drifted
            profile.role       = data['role']
            profile.department = dept
            profile.is_active  = True

            # Wire employee → manager
            if data['role'] == 'manager':
                manager_user_obj = user
            if data['role'] == 'employee' and manager_user_obj:
                profile.manager = manager_user_obj

            profile.save()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test users ready:'))
        self.stdout.write('')
        self.stdout.write('  Role       Username       Password')
        self.stdout.write('  ─────────  ─────────────  ────────────')
        for d in TEST_USERS:
            self.stdout.write(f"  {d['role']:<10} {d['username']:<14} {d['password']}")
        self.stdout.write('')
