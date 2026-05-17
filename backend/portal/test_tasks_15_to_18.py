"""
Tests for Tasks 15-18:
- Task 15: Goal approval workflow
- Task 16: Inline editing during approval review
- Task 17: Cycle management (Admin only)
- Task 18: Cycle-based constraints
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, CheckIn, AuditLog, Notification
)


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

        self.cycle = Cycle.objects.create(
            name='FY2024', status='active',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        self.cycle.set_checkin_dates()
        self.cycle.save()

        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
        self.uom_type, _ = UoMType.objects.get_or_create(name='numeric')

        self.client = APIClient()


# ============================================================================
# Task 15: Goal Approval Workflow
# ============================================================================

class GoalSubmitTests(BaseTestSetup):
    """Tests for POST /api/goals/{id}/submit/"""

    def _make_goal(self, weightage=100, status='draft'):
        return Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Test Goal', target_value=100,
            weightage=weightage, thrust_area=self.thrust_area,
            uom_type=self.uom_type, status=status
        )

    def test_employee_can_submit_own_draft_goal(self):
        goal = self._make_goal()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'submitted')

    def test_submit_requires_100_percent_total_weightage(self):
        """Submitting fails when total weightage != 100."""
        goal = self._make_goal(weightage=50)
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('weightage', response.data['error'].lower())

    def test_cannot_submit_already_submitted_goal(self):
        goal = self._make_goal(status='submitted')
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employee_cannot_submit_other_employees_goal(self):
        other = User.objects.create_user(username='other', password='pass')
        UserProfile.objects.create(user=other, role='employee', department=self.dept)
        goal = Goal.objects.create(
            user=other, cycle=self.cycle, title='Other Goal',
            target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/submit/')
        # Either 403 (permission denied) or 404 (not visible) is acceptable
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND
        ])

    def test_submit_sends_notification_to_manager(self):
        goal = self._make_goal()
        self.client.force_authenticate(user=self.employee_user)
        self.client.post(f'/api/goals/{goal.id}/submit/')
        notif = Notification.objects.filter(
            user=self.manager_user, notification_type='goal_submitted'
        )
        self.assertTrue(notif.exists())


class GoalPendingTests(BaseTestSetup):
    """Tests for GET /api/goals/pending/"""

    def _make_submitted_goal(self, user=None):
        user = user or self.employee_user
        return Goal.objects.create(
            user=user, cycle=self.cycle, title='Pending Goal',
            target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='submitted'
        )

    def test_manager_can_view_pending_goals(self):
        self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/goals/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(data), 1)

    def test_admin_can_view_all_pending_goals(self):
        self._make_submitted_goal()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/goals/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertGreaterEqual(len(data), 1)

    def test_employee_cannot_view_pending_goals(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/goals/pending/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_only_sees_own_team_pending_goals(self):
        """Manager should not see pending goals from other teams."""
        other_manager = User.objects.create_user(username='mgr2', password='pass')
        UserProfile.objects.create(user=other_manager, role='manager')
        other_emp = User.objects.create_user(username='emp2', password='pass')
        UserProfile.objects.create(
            user=other_emp, role='employee', manager=other_manager
        )
        Goal.objects.create(
            user=other_emp, cycle=self.cycle, title='Other Team Goal',
            target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='submitted'
        )
        self._make_submitted_goal()  # own team goal
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/goals/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Should only see own team's goal
        for goal_data in data:
            self.assertNotEqual(goal_data['user_name'], 'emp2')

    def test_pending_only_returns_submitted_goals(self):
        """Pending endpoint should only return submitted goals, not draft/approved."""
        Goal.objects.create(
            user=self.employee_user, cycle=self.cycle, title='Draft Goal',
            target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='draft'
        )
        self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/goals/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for goal_data in data:
            self.assertEqual(goal_data['status'], 'submitted')


class GoalApproveTests(BaseTestSetup):
    """Tests for POST /api/goals/{id}/approve/"""

    def _make_submitted_goal(self):
        return Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Test Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='submitted'
        )

    def test_manager_can_approve_submitted_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'approved')
        self.assertEqual(goal.approved_by, self.manager_user)
        self.assertIsNotNone(goal.approved_at)

    def test_admin_can_approve_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'approved')

    def test_employee_cannot_approve_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_with_comments(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(
            f'/api/goals/{goal.id}/approve/',
            {'approval_comments': 'Looks good!'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.approval_comments, 'Looks good!')

    def test_cannot_approve_draft_goal(self):
        goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Draft', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='draft'
        )
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_creates_audit_log(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.post(f'/api/goals/{goal.id}/approve/')
        logs = AuditLog.objects.filter(
            entity_type='goal', entity_id=goal.id, action='approve'
        )
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().user, self.manager_user)

    def test_approve_sends_notification_to_employee(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.post(f'/api/goals/{goal.id}/approve/')
        notif = Notification.objects.filter(
            user=self.employee_user, notification_type='goal_approved'
        )
        self.assertTrue(notif.exists())


class GoalRejectTests(BaseTestSetup):
    """Tests for POST /api/goals/{id}/reject/"""

    def _make_submitted_goal(self):
        return Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Test Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='submitted'
        )

    def test_manager_can_reject_submitted_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'Target too high'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'rejected')
        self.assertEqual(goal.rejection_reason, 'Target too high')

    def test_reject_requires_reason(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/goals/{goal.id}/reject/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employee_cannot_reject_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'test'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_reject_draft_goal(self):
        goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Draft', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='draft'
        )
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'test'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_creates_audit_log(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'Not aligned'}
        )
        logs = AuditLog.objects.filter(
            entity_type='goal', entity_id=goal.id, action='reject'
        )
        self.assertTrue(logs.exists())

    def test_reject_sends_notification_to_employee(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'Not aligned'}
        )
        notif = Notification.objects.filter(
            user=self.employee_user, notification_type='goal_rejected'
        )
        self.assertTrue(notif.exists())

    def test_admin_can_reject_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f'/api/goals/{goal.id}/reject/',
            {'rejection_reason': 'Admin rejection'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# Task 16: Inline Editing During Approval Review
# ============================================================================

class InlineEditingTests(BaseTestSetup):
    """Tests for PATCH /api/goals/{id}/edit_during_review/"""

    def _make_submitted_goal(self, is_shared=False):
        return Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Original Title', description='Original desc',
            target_value=100000, weightage=50,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='submitted', is_shared=is_shared,
            is_readonly_title=is_shared, is_readonly_target=is_shared
        )

    def test_manager_can_edit_submitted_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Updated Title', 'target_value': 150000},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.title, 'Updated Title')
        self.assertEqual(goal.target_value, 150000)

    def test_admin_can_edit_submitted_goal(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'weightage': 60}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_use_inline_edit(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Hacked'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_inline_edit_draft_goal(self):
        goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Draft', target_value=100, weightage=50,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='draft'
        )
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Updated'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_inline_edit_approved_goal(self):
        goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Approved', target_value=100, weightage=50,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='approved'
        )
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Updated'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inline_edit_creates_audit_trail(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'New Title'}, format='json'
        )
        logs = AuditLog.objects.filter(
            entity_type='goal', entity_id=goal.id, action='update'
        )
        self.assertTrue(logs.exists())
        log = logs.latest('created_at')
        self.assertEqual(log.old_values['title'], 'Original Title')
        self.assertEqual(log.new_values['title'], 'New Title')
        self.assertIn('inline edit', log.comments.lower())

    def test_inline_edit_sends_notification_to_employee(self):
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'New Title'}, format='json'
        )
        notif = Notification.objects.filter(user=self.employee_user, goal=goal)
        self.assertTrue(notif.exists())

    def test_cannot_edit_shared_goal_title(self):
        goal = self._make_submitted_goal(is_shared=True)
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'New Title'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('read-only', response.data['error'].lower())

    def test_cannot_edit_shared_goal_target(self):
        goal = self._make_submitted_goal(is_shared=True)
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'target_value': 999999}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_goal_status_remains_submitted_after_inline_edit(self):
        """Inline edit should not change goal status."""
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Updated'}, format='json'
        )
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'submitted')

    def test_inline_edit_then_approve_workflow(self):
        """Full workflow: edit inline then approve."""
        goal = self._make_submitted_goal()
        self.client.force_authenticate(user=self.manager_user)
        # Edit
        self.client.patch(
            f'/api/goals/{goal.id}/edit_during_review/',
            {'title': 'Revised Title', 'target_value': 120000},
            format='json'
        )
        # Approve
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'approved')
        self.assertEqual(goal.title, 'Revised Title')


# ============================================================================
# Task 17: Cycle Management (Admin only)
# ============================================================================

class CycleListTests(BaseTestSetup):
    """Tests for GET /api/cycles/"""

    def test_admin_can_list_cycles(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/cycles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_cannot_list_cycles(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/cycles/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_list_cycles(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/cycles/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_all_cycles_with_status(self):
        Cycle.objects.create(
            name='FY2025', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/cycles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Should include both cycles (setUp creates one)
        self.assertGreaterEqual(len(data), 2)
        statuses = [c['status'] for c in data]
        self.assertIn('active', statuses)
        self.assertIn('planning', statuses)


class CycleCreateTests(BaseTestSetup):
    """Tests for POST /api/cycles/"""

    def test_admin_can_create_cycle(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'FY2025',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        }
        response = self.client.post('/api/cycles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'FY2025')
        self.assertEqual(response.data['status'], 'planning')

    def test_cycle_creation_auto_sets_checkin_dates(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'FY2025',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        }
        response = self.client.post('/api/cycles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cycle = Cycle.objects.get(id=response.data['id'])
        self.assertIsNotNone(cycle.checkin_date_q1)
        self.assertIsNotNone(cycle.checkin_date_q2)
        self.assertIsNotNone(cycle.checkin_date_q3)
        self.assertIsNotNone(cycle.checkin_date_q4)
        # Verify months
        self.assertEqual(cycle.checkin_date_q1.month, 7)   # July
        self.assertEqual(cycle.checkin_date_q2.month, 10)  # October
        self.assertEqual(cycle.checkin_date_q3.month, 1)   # January
        self.assertEqual(cycle.checkin_date_q4.month, 4)   # April

    def test_cycle_creation_logs_audit_trail(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'FY2025',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        }
        response = self.client.post('/api/cycles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        logs = AuditLog.objects.filter(
            entity_type='cycle', entity_id=response.data['id'], action='create'
        )
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().user, self.admin_user)

    def test_non_admin_cannot_create_cycle(self):
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'name': 'FY2025',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        }
        response = self.client.post('/api/cycles/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_new_cycle_defaults_to_planning_status(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'FY2026',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31'
        }
        response = self.client.post('/api/cycles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'planning')


class CycleActivateTests(BaseTestSetup):
    """Tests for POST /api/cycles/{id}/activate/"""

    def test_admin_can_activate_planning_cycle(self):
        cycle = Cycle.objects.create(
            name='New Cycle', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, 'active')

    def test_cannot_activate_already_active_cycle(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{self.cycle.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_activate_closed_cycle(self):
        cycle = Cycle.objects.create(
            name='Closed Cycle', status='closed',
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_activate_cycle(self):
        cycle = Cycle.objects.create(
            name='New Cycle', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activate_logs_audit_trail(self):
        cycle = Cycle.objects.create(
            name='New Cycle', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(f'/api/cycles/{cycle.id}/activate/')
        logs = AuditLog.objects.filter(
            entity_type='cycle', entity_id=cycle.id, action='update'
        )
        self.assertTrue(logs.exists())
        log = logs.first()
        self.assertEqual(log.old_values['status'], 'planning')
        self.assertEqual(log.new_values['status'], 'active')


class CycleCloseTests(BaseTestSetup):
    """Tests for POST /api/cycles/{id}/close/"""

    def test_admin_can_close_active_cycle(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{self.cycle.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, 'closed')

    def test_cannot_close_planning_cycle(self):
        cycle = Cycle.objects.create(
            name='Planning Cycle', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_close_already_closed_cycle(self):
        cycle = Cycle.objects.create(
            name='Closed Cycle', status='closed',
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/cycles/{cycle.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_close_cycle(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/cycles/{self.cycle.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_close_logs_audit_trail(self):
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(f'/api/cycles/{self.cycle.id}/close/')
        logs = AuditLog.objects.filter(
            entity_type='cycle', entity_id=self.cycle.id, action='update'
        )
        self.assertTrue(logs.exists())
        log = logs.latest('created_at')
        self.assertEqual(log.old_values['status'], 'active')
        self.assertEqual(log.new_values['status'], 'closed')

    def test_full_cycle_state_machine(self):
        """Planning → Active → Closed, no reverse."""
        cycle = Cycle.objects.create(
            name='State Machine Test', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.admin_user)
        # Planning → Active
        r = self.client.post(f'/api/cycles/{cycle.id}/activate/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Active → Closed
        r = self.client.post(f'/api/cycles/{cycle.id}/close/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # Closed → Active (should fail)
        r = self.client.post(f'/api/cycles/{cycle.id}/activate/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Task 18: Cycle-Based Constraints
# ============================================================================

class CycleConstraintsGoalTests(BaseTestSetup):
    """Tests for cycle-based constraints on goal creation."""

    def _goal_data(self, cycle):
        return {
            'title': 'Test Goal',
            'description': 'A goal',
            'cycle': cycle.id,
            'thrust_area': self.thrust_area.id,
            'uom_type': self.uom_type.id,
            'target_value': 100,
            'weightage': 100
        }

    def test_goal_creation_allowed_in_active_cycle(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/goals/', self._goal_data(self.cycle))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_goal_creation_prevented_in_planning_cycle(self):
        planning_cycle = Cycle.objects.create(
            name='Planning', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/goals/', self._goal_data(planning_cycle))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('active', response.data['error'].lower())

    def test_goal_creation_prevented_in_closed_cycle(self):
        closed_cycle = Cycle.objects.create(
            name='Closed', status='closed',
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 12, 31).date()
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/goals/', self._goal_data(closed_cycle))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('active', response.data['error'].lower())

    def test_error_message_mentions_cycle_status(self):
        planning_cycle = Cycle.objects.create(
            name='Planning2', status='planning',
            start_date=datetime(2025, 6, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/goals/', self._goal_data(planning_cycle))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error should mention cycle status
        self.assertIn('cycle', response.data['error'].lower())


class CycleConstraintsCheckInTests(BaseTestSetup):
    """Tests for cycle-based constraints on check-in submissions."""

    def setUp(self):
        super().setUp()
        # Create an approved goal for check-in tests
        self.approved_goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Approved Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='approved', approved_by=self.manager_user,
            approved_at=timezone.now()
        )

    def test_checkin_prevented_in_planning_cycle(self):
        planning_cycle = Cycle.objects.create(
            name='Planning', status='planning',
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date()
        )
        # Create an approved goal in planning cycle
        goal = Goal.objects.create(
            user=self.employee_user, cycle=planning_cycle,
            title='Goal in Planning', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='approved', approved_by=self.manager_user,
            approved_at=timezone.now()
        )
        self.client.force_authenticate(user=self.employee_user)
        data = {
            'goal': goal.id,
            'cycle': planning_cycle.id,
            'progress_value': 50,
            'comments': 'Progress update'
        }
        response = self.client.post('/api/checkins/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('active', response.data['error'].lower())

    def test_checkin_prevented_in_closed_cycle(self):
        closed_cycle = Cycle.objects.create(
            name='Closed', status='closed',
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 12, 31).date()
        )
        goal = Goal.objects.create(
            user=self.employee_user, cycle=closed_cycle,
            title='Goal in Closed', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='approved', approved_by=self.manager_user,
            approved_at=timezone.now()
        )
        self.client.force_authenticate(user=self.employee_user)
        data = {
            'goal': goal.id,
            'cycle': closed_cycle.id,
            'progress_value': 50,
            'comments': 'Progress update'
        }
        response = self.client.post('/api/checkins/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('active', response.data['error'].lower())

    def test_checkin_requires_approved_goal(self):
        """Check-in should fail for non-approved goals."""
        draft_goal = Goal.objects.create(
            user=self.employee_user, cycle=self.cycle,
            title='Draft Goal', target_value=100, weightage=100,
            thrust_area=self.thrust_area, uom_type=self.uom_type,
            status='draft'
        )
        self.client.force_authenticate(user=self.employee_user)
        data = {
            'goal': draft_goal.id,
            'cycle': self.cycle.id,
            'progress_value': 50,
            'comments': 'Progress update'
        }
        response = self.client.post('/api/checkins/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('approved', response.data['error'].lower())

    def test_checkin_allowed_in_active_cycle_for_approved_goal(self):
        """Check-in should succeed for approved goal in active cycle."""
        # Set a check-in date that includes today so the period validation passes
        from django.utils import timezone
        today = timezone.now().date()
        self.cycle.checkin_date_q1 = today
        self.cycle.save()

        self.client.force_authenticate(user=self.employee_user)
        data = {
            'goal': self.approved_goal.id,
            'cycle': self.cycle.id,
            'progress_value': 50,
            'comments': 'Progress update'
        }
        response = self.client.post('/api/checkins/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_checkin_calculates_progress_percentage(self):
        """Check-in should calculate progress percentage."""
        # Set a check-in date that includes today
        from django.utils import timezone
        today = timezone.now().date()
        self.cycle.checkin_date_q1 = today
        self.cycle.save()

        self.client.force_authenticate(user=self.employee_user)
        data = {
            'goal': self.approved_goal.id,
            'cycle': self.cycle.id,
            'progress_value': 50,  # 50% of target 100
            'comments': 'Half done'
        }
        response = self.client.post('/api/checkins/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['progress_percentage'], 50.0)
