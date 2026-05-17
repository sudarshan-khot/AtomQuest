#!/usr/bin/env python
"""
Script to run validator tests manually.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atomquest.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

# Now run tests
from django.test.utils import get_runner
from django.conf import settings

TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
failures = test_runner.run_tests(['portal.test_validators'])
sys.exit(bool(failures))
