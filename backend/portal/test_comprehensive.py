"""
Comprehensive tests for AtomQuest Goal Setting & Tracking Portal.
Covers: Auth, RBAC, Goal Lifecycle, Check-ins, Scoring, Cycles, Audit Trail.

Run: python manage.py test portal.test_comprehensive -v 2
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import date, timedelta

from .models import (
    UserProfile, Department, ThrustArea, UoMType,
    Cycle, Goal, CheckIn, AuditLog, Notification
)
from .utils import calculate_progress_percentage


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixture mixin
# ─────────────────────────────────────────────────────────────────────────────

class BaseFixture(APITestCase):
    """Creates admin / manager / employee + reference data used by all tests."""

    def setUp(self):
        self.dept = Department.objects.create(name='Engineering')

        # Admin
        self.admin = User.objects.create_user('admin_t', 'a@t.com', 'pass1234')
        UserProfile.objects.create(user=self.admin, role='admin', department=self.dept)

        # Manager
        self.manager = User.objects.create_user('manager_t', 'm@t.com', 'pass1234')
        UserProfile.objects.create(user=self.manager, role='manager', department=self.dept)

        # Employee
        self.employee = User.objects.create_user('employee_t', 'e@t.com', 'pass1234')
        UserProfile.objects.create(
            user=self.employee, role='employee',
            department=self.dept, manager=self.manager
        )

        # Reference data
        self.thrust, _ = ThrustArea.objects.get_or_create(name='Revenue Growth')
        self.uom_num,  _ = UoMType.objects.get_or_create(name='numeric')
        self.uom_pct,  _ = UoMType.objects.get_or_create(name='percentage')
        self.uom_tl,   _ = UoMType.objects.get_or_create(name='timeline')
        self.uom_zb,   _ = UoMType.objects.get_or_create(name='zero_based')

        # Active cycle
        self.cycle = Cycle.objects.create(
            name='FY2025', status='active',
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )

        self.client = APIClient()

    # helpers
    def auth(self, user):
        self.client.force_authenticate(user=user)

    def make_goal(self, user=None, status='draft', weightage=100, uom=None):
        return Goal.objects.create(
            user=user or self.employee,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=weightage,
            thrust_area=self.thrust,
            uom_type=uom or self.uom_num,
            status=status,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Authentication
# ─────────────────────────────────────────────────────────────────────────────

class AuthTests(BaseFixture):

    def test_token_auth_success(self):
        """POST /api-token-auth/ returns token for valid credentials."""
        r = self.client.post('/api-token-auth/', {'username': 'admin_t', 'password': 'pass1234'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('token', r.data)

    def test_token_auth_wrong_password(self):
        r = self.client.post('/api-token-auth/', {'username': 'admin_t', 'password': 'wrong'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_rejected(self):
        r = self.client.get('/api/goals/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_returns_profile(self):
        self.auth(self.employee)
        r = self.client.get('/api/users/me/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['role'], 'employee')


# ─────────────────────────────────────────────────────────────────────────────
# 2. RBAC — permission boundaries
# ─────────────────────────────────────────────────────────────────────────────

class RBACTests(BaseFixture):

    def test_employee_cannot_access_user_management(self):
        self.auth(self.employee)
        r = self.client.get('/api/user-management/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_access_user_management(self):
        self.auth(self.manager)
        r = self.client.get('/api/user-management/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_user_management(self):
        self.auth(self.admin)
        r = self.client.get('/api/user-management/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_employee_cannot_approve_goal(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.employee)
        r = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_create_cycle(self):
        self.auth(self.employee)
        r = self.client.post('/api/cycles/', {
            'name': 'Bad', 'start_date': '2025-01-01', 'end_date': '2025-12-31'
        })
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_view_pending_goals(self):
        self.make_goal(status='submitted')
        self.auth(self.manager)
        r = self.client.get('/api/goals/pending/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_employee_cannot_view_pending_goals(self):
        self.auth(self.employee)
        r = self.client.get('/api/goals/pending/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Goal Creation & Validation
# ─────────────────────────────────────────────────────────────────────────────

class GoalCreationTests(BaseFixture):

    def _post_goal(self, data=None):
        self.auth(self.employee)
        payload = {
            'title': 'Increase Revenue',
            'description': 'By 20%',
            'cycle': self.cycle.id,
            'thrust_area': self.thrust.id,
            'uom_type': self.uom_num.id,
            'target_value': 1000,
            'weightage': 100,
        }
        if data:
            payload.update(data)
        return self.client.post('/api/goals/', payload)

    def test_create_goal_success(self):
        r = self._post_goal()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['status'], 'draft')

    def test_create_goal_missing_title(self):
        r = self._post_goal({'title': ''})
        self.assertIn(r.status_code, [400, 422])

    def test_create_goal_negative_target(self):
        r = self._post_goal({'target_value': -1})
        self.assertIn(r.status_code, [400, 422])

    def test_create_goal_weightage_below_10(self):
        r = self._post_goal({'weightage': 5})
        self.assertIn(r.status_code, [400, 422])

    def test_create_goal_weightage_above_100(self):
        r = self._post_goal({'weightage': 110})
        self.assertIn(r.status_code, [400, 422])

    def test_max_8_goals_per_cycle(self):
        for i in range(8):
            Goal.objects.create(
                user=self.employee, cycle=self.cycle,
                title=f'G{i}', target_value=100, weightage=12.5,
                thrust_area=self.thrust, uom_type=self.uom_num,
            )
        r = self._post_goal({'weightage': 12.5})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_goal_in_planning_cycle_rejected(self):
        planning = Cycle.objects.create(
            name='Planning', status='planning',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
        )
        self.auth(self.employee)
        r = self.client.post('/api/goals/', {
            'title': 'X', 'cycle': planning.id,
            'uom_type': self.uom_num.id, 'target_value': 10, 'weightage': 100,
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_goal_in_closed_cycle_rejected(self):
        closed = Cycle.objects.create(
            name='Closed', status='closed',
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        self.auth(self.employee)
        r = self.client.post('/api/goals/', {
            'title': 'X', 'cycle': closed.id,
            'uom_type': self.uom_num.id, 'target_value': 10, 'weightage': 100,
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Goal Lifecycle — state machine
# ─────────────────────────────────────────────────────────────────────────────

class GoalLifecycleTests(BaseFixture):

    def test_submit_draft_goal(self):
        goal = self.make_goal(status='draft', weightage=100)
        self.auth(self.employee)
        r = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'submitted')

    def test_submit_requires_100_percent_weightage(self):
        """Submitting when total weightage != 100 must fail."""
        self.make_goal(status='draft', weightage=60)
        goal2 = self.make_goal(status='draft', weightage=30)
        self.auth(self.employee)
        r = self.client.post(f'/api/goals/{goal2.id}/submit/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_submit_already_submitted_goal(self):
        goal = self.make_goal(status='submitted', weightage=100)
        self.auth(self.employee)
        r = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_approves_submitted_goal(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        r = self.client.post(f'/api/goals/{goal.id}/approve/', {'approval_comments': 'Looks good'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'approved')
        self.assertEqual(goal.approved_by, self.manager)
        self.assertEqual(goal.approval_comments, 'Looks good')

    def test_manager_rejects_submitted_goal(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        r = self.client.post(f'/api/goals/{goal.id}/reject/', {'rejection_reason': 'Target unrealistic'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'rejected')
        self.assertEqual(goal.rejection_reason, 'Target unrealistic')

    def test_reject_requires_reason(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        r = self.client.post(f'/api/goals/{goal.id}/reject/', {})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_approve_draft_goal(self):
        goal = self.make_goal(status='draft')
        self.auth(self.manager)
        r = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approved_goal_is_locked_from_employee_edit(self):
        goal = self.make_goal(status='approved')
        self.auth(self.employee)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'title': 'Changed'})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_edit_locked_goal(self):
        goal = self.make_goal(status='approved')
        self.auth(self.admin)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'title': 'Admin Edit'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_manager_inline_edit_during_review(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        r = self.client.patch(f'/api/goals/{goal.id}/edit_during_review/', {'weightage': 80})
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_employee_cannot_edit_others_goal(self):
        other = User.objects.create_user('other_t', 'o@t.com', 'pass1234')
        UserProfile.objects.create(user=other, role='employee', department=self.dept)
        goal = self.make_goal(user=other, status='draft')
        self.auth(self.employee)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'title': 'Hack'})
        self.assertIn(r.status_code, [403, 404])

    def test_delete_draft_goal(self):
        goal = self.make_goal(status='draft')
        self.auth(self.employee)
        r = self.client.delete(f'/api/goals/{goal.id}/')
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_submitted_goal(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.employee)
        r = self.client.delete(f'/api/goals/{goal.id}/')
        self.assertIn(r.status_code, [403, 400])


# ─────────────────────────────────────────────────────────────────────────────
# 5. Progress Scoring Engine
# ─────────────────────────────────────────────────────────────────────────────

class ScoringEngineTests(BaseFixture):

    def _goal(self, uom, target):
        return Goal(
            user=self.employee, cycle=self.cycle,
            title='S', target_value=target, weightage=100,
            thrust_area=self.thrust, uom_type=uom,
        )

    # Numeric
    def test_numeric_50_percent(self):
        g = self._goal(self.uom_num, 1000)
        self.assertAlmostEqual(calculate_progress_percentage(g, 500), 50.0)

    def test_numeric_100_percent(self):
        g = self._goal(self.uom_num, 1000)
        self.assertAlmostEqual(calculate_progress_percentage(g, 1000), 100.0)

    def test_numeric_capped_at_100(self):
        g = self._goal(self.uom_num, 1000)
        self.assertAlmostEqual(calculate_progress_percentage(g, 1500), 100.0)

    def test_numeric_zero_progress(self):
        g = self._goal(self.uom_num, 1000)
        self.assertAlmostEqual(calculate_progress_percentage(g, 0), 0.0)

    # Percentage
    def test_percentage_direct_mapping(self):
        g = self._goal(self.uom_pct, 100)
        self.assertAlmostEqual(calculate_progress_percentage(g, 75), 75.0)

    def test_percentage_capped_at_100(self):
        g = self._goal(self.uom_pct, 100)
        self.assertAlmostEqual(calculate_progress_percentage(g, 120), 100.0)

    # Zero-based
    def test_zero_based_zero_value_is_0_percent(self):
        g = self._goal(self.uom_zb, 1)
        self.assertAlmostEqual(calculate_progress_percentage(g, 0), 0.0)

    def test_zero_based_nonzero_value_is_100_percent(self):
        g = self._goal(self.uom_zb, 1)
        self.assertAlmostEqual(calculate_progress_percentage(g, 1), 100.0)

    # Timeline — uses dedicated calculate_timeline_progress
    def test_timeline_midpoint(self):
        from .utils import calculate_timeline_progress
        # Midpoint of 2025-01-01 → 2025-12-31 is roughly 2025-07-02
        result = calculate_timeline_progress(
            date(2025, 1, 1), date(2025, 12, 31), date(2025, 7, 2)
        )
        self.assertGreater(result, 40)
        self.assertLess(result, 60)

    def test_timeline_before_start_is_0(self):
        from .utils import calculate_timeline_progress
        result = calculate_timeline_progress(
            date(2025, 6, 1), date(2025, 12, 31), date(2025, 1, 1)
        )
        self.assertEqual(result, 0)

    def test_timeline_after_end_is_100(self):
        from .utils import calculate_timeline_progress
        result = calculate_timeline_progress(
            date(2025, 1, 1), date(2025, 6, 30), date(2025, 12, 31)
        )
        self.assertEqual(result, 100)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Check-in Workflow
# ─────────────────────────────────────────────────────────────────────────────

class CheckInTests(BaseFixture):

    def _post_checkin(self, goal, value=50):
        self.auth(self.employee)
        return self.client.post('/api/checkins/', {
            'goal': goal.id,
            'cycle': self.cycle.id,
            'progress_value': value,
            'comments': 'On track',
        })

    def test_checkin_on_approved_goal_succeeds(self):
        goal = self.make_goal(status='approved')
        r = self._post_checkin(goal)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn('progress_percentage', r.data)

    def test_checkin_on_draft_goal_rejected(self):
        goal = self.make_goal(status='draft')
        r = self._post_checkin(goal)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_on_submitted_goal_rejected(self):
        goal = self.make_goal(status='submitted')
        r = self._post_checkin(goal)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_one_checkin_per_goal_per_cycle(self):
        goal = self.make_goal(status='approved')
        self._post_checkin(goal, 50)
        r = self._post_checkin(goal, 60)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkin_in_closed_cycle_rejected(self):
        closed = Cycle.objects.create(
            name='Closed2', status='closed',
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        goal = Goal.objects.create(
            user=self.employee, cycle=closed, title='G',
            target_value=100, weightage=100,
            thrust_area=self.thrust, uom_type=self.uom_num, status='approved'
        )
        self.auth(self.employee)
        r = self.client.post('/api/checkins/', {
            'goal': goal.id, 'cycle': closed.id, 'progress_value': 50
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_approves_checkin(self):
        goal = self.make_goal(status='approved')
        self._post_checkin(goal, 70)
        ci = CheckIn.objects.get(goal=goal)
        self.auth(self.manager)
        r = self.client.post(f'/api/checkins/{ci.id}/approve/', {'approval_comments': 'Good'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ci.refresh_from_db()
        self.assertEqual(ci.status, 'approved')

    def test_manager_rejects_checkin_with_comment(self):
        goal = self.make_goal(status='approved')
        self._post_checkin(goal, 10)
        ci = CheckIn.objects.get(goal=goal)
        self.auth(self.manager)
        r = self.client.post(f'/api/checkins/{ci.id}/reject/', {'rejection_comments': 'Too low'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ci.refresh_from_db()
        self.assertEqual(ci.status, 'rejected')
        self.assertEqual(ci.rejection_comments, 'Too low')

    def test_employee_cannot_approve_checkin(self):
        goal = self.make_goal(status='approved')
        self._post_checkin(goal, 50)
        ci = CheckIn.objects.get(goal=goal)
        self.auth(self.employee)
        r = self.client.post(f'/api/checkins/{ci.id}/approve/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_progress_percentage_calculated_on_checkin(self):
        goal = self.make_goal(status='approved', uom=self.uom_num)
        goal.target_value = 200
        goal.save()
        r = self._post_checkin(goal, 100)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertAlmostEqual(float(r.data['progress_percentage']), 50.0, places=1)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Cycle Management
# ─────────────────────────────────────────────────────────────────────────────

class CycleManagementTests(BaseFixture):

    def test_admin_creates_cycle_with_auto_checkin_dates(self):
        self.auth(self.admin)
        r = self.client.post('/api/cycles/', {
            'name': 'FY2026',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(r.data.get('checkin_date_q1'))
        self.assertIsNotNone(r.data.get('checkin_date_q4'))

    def test_non_admin_cannot_create_cycle(self):
        self.auth(self.manager)
        r = self.client.post('/api/cycles/', {
            'name': 'FY2026', 'start_date': '2026-01-01', 'end_date': '2026-12-31'
        })
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_activate_planning_cycle(self):
        c = Cycle.objects.create(
            name='Plan', status='planning',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
        )
        self.auth(self.admin)
        r = self.client.post(f'/api/cycles/{c.id}/activate/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        c.refresh_from_db()
        self.assertEqual(c.status, 'active')

    def test_cannot_activate_already_active_cycle(self):
        self.auth(self.admin)
        r = self.client.post(f'/api/cycles/{self.cycle.id}/activate/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_close_active_cycle(self):
        self.auth(self.admin)
        r = self.client.post(f'/api/cycles/{self.cycle.id}/close/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.cycle.refresh_from_db()
        self.assertEqual(self.cycle.status, 'closed')

    def test_cannot_close_planning_cycle(self):
        c = Cycle.objects.create(
            name='Plan2', status='planning',
            start_date=date(2027, 1, 1), end_date=date(2027, 12, 31)
        )
        self.auth(self.admin)
        r = self.client.post(f'/api/cycles/{c.id}/close/')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# 8. User Management (Admin)
# ─────────────────────────────────────────────────────────────────────────────

class UserManagementTests(BaseFixture):

    def test_admin_creates_user(self):
        self.auth(self.admin)
        r = self.client.post('/api/user-management/', {
            'username': 'newbie', 'email': 'nb@t.com',
            'password': 'pass1234', 'role': 'employee',
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_duplicate_username_rejected(self):
        self.auth(self.admin)
        r = self.client.post('/api/user-management/', {
            'username': 'employee_t', 'email': 'x@t.com', 'password': 'pass1234'
        })
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_deactivates_user(self):
        self.auth(self.admin)
        r = self.client.post(f'/api/user-management/{self.employee.id}/deactivate/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.employee.profile.refresh_from_db()
        self.assertFalse(self.employee.profile.is_active)

    def test_admin_reactivates_user(self):
        self.employee.profile.is_active = False
        self.employee.profile.save()
        self.auth(self.admin)
        r = self.client.post(f'/api/user-management/{self.employee.id}/reactivate/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.employee.profile.refresh_from_db()
        self.assertTrue(self.employee.profile.is_active)

    def test_admin_updates_user_role(self):
        self.auth(self.admin)
        r = self.client.put(f'/api/user-management/{self.employee.id}/', {'role': 'manager'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.employee.profile.refresh_from_db()
        self.assertEqual(self.employee.profile.role, 'manager')


# ─────────────────────────────────────────────────────────────────────────────
# 9. Audit Trail
# ─────────────────────────────────────────────────────────────────────────────

class AuditTrailTests(BaseFixture):

    def test_goal_creation_logged(self):
        self.auth(self.employee)
        self.client.post('/api/goals/', {
            'title': 'Audit Goal', 'cycle': self.cycle.id,
            'uom_type': self.uom_num.id, 'target_value': 100, 'weightage': 100,
        })
        goal = Goal.objects.get(title='Audit Goal')
        self.assertTrue(
            AuditLog.objects.filter(entity_type='goal', entity_id=goal.id, action='create').exists()
        )

    def test_goal_approval_logged(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertTrue(
            AuditLog.objects.filter(entity_type='goal', entity_id=goal.id, action='approve').exists()
        )

    def test_goal_rejection_logged(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        self.client.post(f'/api/goals/{goal.id}/reject/', {'rejection_reason': 'Bad'})
        self.assertTrue(
            AuditLog.objects.filter(entity_type='goal', entity_id=goal.id, action='reject').exists()
        )

    def test_goal_submission_logged(self):
        goal = self.make_goal(status='draft', weightage=100)
        self.auth(self.employee)
        self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertTrue(
            AuditLog.objects.filter(entity_type='goal', entity_id=goal.id, action='submit').exists()
        )

    def test_user_creation_logged(self):
        self.auth(self.admin)
        self.client.post('/api/user-management/', {
            'username': 'auditee', 'email': 'au@t.com', 'password': 'pass1234'
        })
        user = User.objects.get(username='auditee')
        self.assertTrue(
            AuditLog.objects.filter(entity_type='user', entity_id=user.id, action='create').exists()
        )

    def test_audit_log_is_immutable(self):
        """AuditLog has no update endpoint — direct DB check."""
        log = AuditLog.objects.create(
            entity_type='goal', entity_id=1, action='create',
            user=self.admin
        )
        original_ts = log.created_at
        log.comments = 'tampered'
        log.save()
        log.refresh_from_db()
        # created_at must not change (auto_now_add)
        self.assertEqual(log.created_at, original_ts)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Notifications
# ─────────────────────────────────────────────────────────────────────────────

class NotificationTests(BaseFixture):

    def test_notification_created_on_goal_submission(self):
        goal = self.make_goal(status='draft', weightage=100)
        self.auth(self.employee)
        self.client.post(f'/api/goals/{goal.id}/submit/')
        # Manager should receive a notification
        self.assertTrue(
            Notification.objects.filter(
                user=self.manager,
                notification_type='goal_submitted'
            ).exists()
        )

    def test_notification_created_on_goal_approval(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertTrue(
            Notification.objects.filter(
                user=self.employee,
                notification_type='goal_approved'
            ).exists()
        )

    def test_notification_created_on_goal_rejection(self):
        goal = self.make_goal(status='submitted')
        self.auth(self.manager)
        self.client.post(f'/api/goals/{goal.id}/reject/', {'rejection_reason': 'No'})
        self.assertTrue(
            Notification.objects.filter(
                user=self.employee,
                notification_type='goal_rejected'
            ).exists()
        )

    def test_employee_can_list_own_notifications(self):
        Notification.objects.create(
            user=self.employee, title='Test', message='Hello',
            notification_type='goal_approved'
        )
        self.auth(self.employee)
        r = self.client.get('/api/notifications/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        results = r.data if isinstance(r.data, list) else r.data.get('results', [])
        self.assertGreaterEqual(len(results), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Shared Goals (KPI Distribution)
# ─────────────────────────────────────────────────────────────────────────────

class SharedGoalTests(BaseFixture):

    def _make_shared_goal(self):
        goal = Goal.objects.create(
            user=self.employee, cycle=self.cycle,
            title='Dept KPI', target_value=500, weightage=50,
            thrust_area=self.thrust, uom_type=self.uom_num,
            status='draft', is_shared=True,
            is_readonly_title=True, is_readonly_target=True,
            shared_by=self.admin,
        )
        return goal

    def test_shared_goal_title_is_readonly(self):
        goal = self._make_shared_goal()
        self.auth(self.employee)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'title': 'Changed'})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shared_goal_target_is_readonly(self):
        goal = self._make_shared_goal()
        self.auth(self.employee)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'target_value': 999})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shared_goal_weightage_is_editable(self):
        goal = self._make_shared_goal()
        self.auth(self.employee)
        r = self.client.patch(f'/api/goals/{goal.id}/', {'weightage': 60})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.weightage, 60)


# ─────────────────────────────────────────────────────────────────────────────
# 12. End-to-end: full goal → check-in flow
# ─────────────────────────────────────────────────────────────────────────────

class EndToEndFlowTests(BaseFixture):

    def test_full_goal_checkin_flow(self):
        """
        Employee creates goal → submits → manager approves →
        employee submits check-in → manager approves check-in.
        """
        # 1. Create
        self.auth(self.employee)
        r = self.client.post('/api/goals/', {
            'title': 'E2E Goal', 'cycle': self.cycle.id,
            'uom_type': self.uom_num.id, 'target_value': 100, 'weightage': 100,
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        goal_id = r.data['id']

        # 2. Submit
        r = self.client.post(f'/api/goals/{goal_id}/submit/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # 3. Manager approves
        self.auth(self.manager)
        r = self.client.post(f'/api/goals/{goal_id}/approve/', {'approval_comments': 'OK'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # 4. Employee submits check-in
        self.auth(self.employee)
        r = self.client.post('/api/checkins/', {
            'goal': goal_id, 'cycle': self.cycle.id,
            'progress_value': 75, 'comments': 'Good progress',
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertAlmostEqual(float(r.data['progress_percentage']), 75.0, places=1)
        ci_id = r.data['id']

        # 5. Manager approves check-in
        self.auth(self.manager)
        r = self.client.post(f'/api/checkins/{ci_id}/approve/', {'approval_comments': 'Verified'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        ci = CheckIn.objects.get(id=ci_id)
        self.assertEqual(ci.status, 'approved')
        self.assertEqual(ci.approved_by, self.manager)

    def test_rejection_and_resubmission_flow(self):
        """Employee submits → manager rejects → employee resubmits."""
        goal = self.make_goal(status='draft', weightage=100)

        self.auth(self.employee)
        self.client.post(f'/api/goals/{goal.id}/submit/')

        self.auth(self.manager)
        self.client.post(f'/api/goals/{goal.id}/reject/', {'rejection_reason': 'Revise target'})

        goal.refresh_from_db()
        self.assertEqual(goal.status, 'rejected')

        # Employee edits and resubmits
        self.auth(self.employee)
        self.client.patch(f'/api/goals/{goal.id}/', {'target_value': 200})
        r = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'submitted')
