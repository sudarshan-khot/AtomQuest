#!/usr/bin/env python
"""
Manual test script to verify validators work correctly.
Run with: python test_validators_manual.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atomquest.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta

from portal.models import UoMType, Cycle, Goal
from portal.validators import (
    validate_numeric_progress,
    validate_percentage_progress,
    validate_zero_based_progress,
    validate_email_format,
    validate_date_format,
    validate_goal_approved_for_checkin,
    validate_cycle_active_for_checkin,
)

def test_numeric_progress():
    """Test numeric progress validation."""
    print("\n=== Testing Numeric Progress Validation ===")
    try:
        is_valid, _ = validate_numeric_progress(50, 100)
        print("✓ Valid numeric progress (50/100): PASS")
    except Exception as e:
        print(f"✗ Valid numeric progress: FAIL - {e}")
    
    try:
        validate_numeric_progress(150, 100)
        print("✗ Invalid numeric progress (150/100): FAIL - should have raised error")
    except ValidationError:
        print("✓ Invalid numeric progress (150/100): PASS")

def test_percentage_progress():
    """Test percentage progress validation."""
    print("\n=== Testing Percentage Progress Validation ===")
    try:
        is_valid, _ = validate_percentage_progress(75)
        print("✓ Valid percentage progress (75%): PASS")
    except Exception as e:
        print(f"✗ Valid percentage progress: FAIL - {e}")
    
    try:
        validate_percentage_progress(150)
        print("✗ Invalid percentage progress (150%): FAIL - should have raised error")
    except ValidationError:
        print("✓ Invalid percentage progress (150%): PASS")

def test_email_format():
    """Test email format validation."""
    print("\n=== Testing Email Format Validation ===")
    try:
        is_valid, _ = validate_email_format('user@example.com')
        print("✓ Valid email (user@example.com): PASS")
    except Exception as e:
        print(f"✗ Valid email: FAIL - {e}")
    
    try:
        validate_email_format('invalid-email')
        print("✗ Invalid email (invalid-email): FAIL - should have raised error")
    except ValidationError:
        print("✓ Invalid email (invalid-email): PASS")

def test_date_format():
    """Test date format validation."""
    print("\n=== Testing Date Format Validation ===")
    try:
        is_valid, _, parsed = validate_date_format('2024-01-15')
        print(f"✓ Valid date (2024-01-15): PASS - parsed as {parsed}")
    except Exception as e:
        print(f"✗ Valid date: FAIL - {e}")
    
    try:
        validate_date_format('2024-02-30')
        print("✗ Invalid date (2024-02-30): FAIL - should have raised error")
    except ValidationError:
        print("✓ Invalid date (2024-02-30): PASS")

def test_goal_approval():
    """Test goal approval validation."""
    print("\n=== Testing Goal Approval Validation ===")
    
    # Create test data
    uom = UoMType.objects.first() or UoMType.objects.create(name='numeric')
    user = User.objects.first() or User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123'
    )
    cycle = Cycle.objects.first() or Cycle.objects.create(
        name='Test Cycle',
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    
    # Test approved goal
    goal_approved = Goal.objects.create(
        user=user,
        cycle=cycle,
        title='Approved Goal',
        target_value=100,
        weightage=50,
        uom_type=uom,
        status='approved'
    )
    
    try:
        is_valid, _ = validate_goal_approved_for_checkin(goal_approved)
        print("✓ Approved goal validation: PASS")
    except Exception as e:
        print(f"✗ Approved goal validation: FAIL - {e}")
    
    # Test draft goal
    goal_draft = Goal.objects.create(
        user=user,
        cycle=cycle,
        title='Draft Goal',
        target_value=100,
        weightage=50,
        uom_type=uom,
        status='draft'
    )
    
    try:
        validate_goal_approved_for_checkin(goal_draft)
        print("✗ Draft goal validation: FAIL - should have raised error")
    except ValidationError:
        print("✓ Draft goal validation: PASS")

def test_cycle_active():
    """Test cycle active validation."""
    print("\n=== Testing Cycle Active Validation ===")
    
    # Create test data
    cycle_active = Cycle.objects.create(
        name='Active Cycle',
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status='active'
    )
    
    try:
        is_valid, _ = validate_cycle_active_for_checkin(cycle_active)
        print("✓ Active cycle validation: PASS")
    except Exception as e:
        print(f"✗ Active cycle validation: FAIL - {e}")
    
    # Test planning cycle
    cycle_planning = Cycle.objects.create(
        name='Planning Cycle',
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status='planning'
    )
    
    try:
        validate_cycle_active_for_checkin(cycle_planning)
        print("✗ Planning cycle validation: FAIL - should have raised error")
    except ValidationError:
        print("✓ Planning cycle validation: PASS")

if __name__ == '__main__':
    print("=" * 60)
    print("VALIDATOR MANUAL TEST SUITE")
    print("=" * 60)
    
    test_numeric_progress()
    test_percentage_progress()
    test_email_format()
    test_date_format()
    test_goal_approval()
    test_cycle_active()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
