#!/usr/bin/env python
"""
Simple test runner for RBAC tests.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atomquest.settings')
django.setup()

# Run tests
from django.core.management import call_command
call_command('test', 'portal.test_rbac', verbosity=2)
