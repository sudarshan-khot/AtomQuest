"""
Tests for Tasks 19-22:
- Task 19: Check-in creation and submission
- Task 20: Quarterly check-in cycle management
- Task 21: Check-in approval workflow
- Task 22: Audit trail logging system
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, date
from unittest.mock import patch
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, CheckIn, AuditLog, Notification
)
from .utils import (
    log_audit_trail, calculate_progress_percentage,
    validate_checkin_period, get_client_ip
)
from .validators import CheckInValidator


# ============================================================================
# Shared setUp mixin
# ============================================================================

class BaseTestSetup(APITestCase):
    """Base class with common test setup."""

    def setUp(self):
        self.dept = Department.objects.create(name='Engineering')

        self.admin_user = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')

        self.manager_user = User.objects.create_user(
            username='manager', email='manager@test.com', password='testpass123'
        )
        UserProfile.objects.create(
            user=self.manager_user, role='manager', department=self.dept
        )

        self.employee_user = User.objects.create_user(
            username='employee', email='employee@test.com', password='testpass123'
        )
        UserProfile.objects.create(
            user=self.employee_user, role='employee',
            department=self.dept, manager=self.manager_user
        )

        # Active cycle with check-in dates set
        self.cycle = Cycle.objects.create(
            name='FY2024', status='active',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        self.cycle.set_checkin_dates()
        self.cycle.save()

        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
        self.uom_numeric, _ = UoMType.objects.get_or_create(name='numeric')
        self.uom_percentage, _ = UoMType.objects.get_or_create(name='percentage')
        self.uom_zero_based, _ = UoMType.objects.get_or_create(name='zero_based')

        self.client = APIClient()

    def _make_approved_goal(self, user=None, uom_type=None, target_value=100,
                             weightage=100):
        user = user or self.employee_user
        uom_type = uom_type or self.uom_numeric
        return Goal.objects.create(
            user=user, cycle=self.cycle,
            title='Approved Goal', target_value=target_value,
            weightage=weightage, thrust_area=self.thrust_area,
            uom_type=uom_type, status='approved'
        )

    def _make_submitted_checkin(self, goal=None, progress_value=50):
        goal = goal or self._make_approved_goal()
        return CheckIn.objects.create(
            goal=goal, user=self.employee_user, cycle=self.cycle,
            progress_value=progress_value,
            progress_percentage=calculate_progress_percentage(goal, progress_value),
            status='submitted'
        )

    def _active_checkin_date(self):
        """Return a date that falls within the Q1 check-in window."""
        return self.cycle.checkin_date_q1  # exactly on the check-in date


# ============================================================================
# Task 19: Approved Goals Endpoint
# ============================================================================

class ApprovedGoalsEndpointTests(BaseTestSetup):
    """Tests for GET /api/checkins/approved_goals/"""

    def test_returns_approved_goals_for_current_user(self):
        goal = self._make_approved_goal()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/checkins/approved_goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [g['id'] for g in response.data]
        self.assertIn(goal.id, ids)

    def test_does_not_return_draft_goals(self):
        Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Draft Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_numeric,
            status='draft'
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/checkins/approved_goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for g in response.data:
            self.assertEqual(g['status'], 'approved')

    def test_does_not_return_other_users_goals(self):
        other = User.objects.create_user(username='other2', password='pass')
        UserProfile.objects.create(user=other, role='employee', department=self.dept)
        Goal.objects.create(
            user=other, cycle=self.cycle, title='Other Goal',
            target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_numeric,
            status='approved'
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/checkins/approved_goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for g in response.data:
            self.assertEqual(g['user_name'], 'employee')

    def test_requires_authentication(self):
        response = self.client.get('/api/checkins/approved_goals/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_return_goals_from_inactive_cycles(self):
        closed_cycle = Cycle.objects.create(
            name='Closed', status='closed',
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 12, 31).date()
        )
        Goal.objects.create(
            user=self.employee_user, cycle=closed_cycle,
            title='Old Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_numeric,
            status='approved'
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/checkins/approved_goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for g in response.data:
            self.assertNotEqual(g.get('cycle'), closed_cycle.id)
