"""
Tests for the AtomQuest Goal Setting & Tracking Portal.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, SharedGoal, CheckIn, AuditLog, Notification
)
from .utils import (
    calculate_progress_percentage, validate_weightage, validate_goal_count,
    validate_checkin_period, calculate_weighted_achievement
)


# ============================================================================
# Phase 2: RBAC and User Management Tests
# ============================================================================

class UserProfileTestCase(APITestCase):
    """Test cases for user profile and RBAC."""
    
    def setUp(self):
        """Set up test data."""
        # Create departments
        self.dept_sales = Department.objects.create(name='Sales')
        self.dept_eng = Department.objects.create(name='Engineering')
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.dept_sales
        )
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.dept_sales,
            manager=self.manager_user
        )
        
        self.client = APIClient()
    
    def test_user_profile_creation(self):
        """Test that user profiles are created correctly."""
        self.assertEqual(self.admin_profile.role, 'admin')
        self.assertEqual(self.manager_profile.role, 'manager')
        self.assertEqual(self.employee_profile.role, 'employee')
        self.assertTrue(self.admin_profile.is_active)
    
    def test_user_profile_hierarchy(self):
        """Test manager-employee hierarchy."""
        self.assertEqual(self.employee_profile.manager, self.manager_user)
        self.assertEqual(self.employee_profile.department, self.dept_sales)
    
    def test_admin_can_view_all_users(self):
        """Test that admin can view all users."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_manager_can_view_team(self):
        """Test that manager can view their team."""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/users/team/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_employee_can_view_own_profile(self):
        """Test that employee can view their own profile."""
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_deactivation(self):
        """Test user deactivation by admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/users/{self.employee_profile.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_profile.refresh_from_db()
        self.assertFalse(self.employee_profile.is_active)
    
    def test_user_reactivation(self):
        """Test user reactivation by admin."""
        self.employee_profile.is_active = False
        self.employee_profile.save()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/users/{self.employee_profile.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_profile.refresh_from_db()
        self.assertTrue(self.employee_profile.is_active)


class UserManagementTestCase(APITestCase):
    """Test cases for user management operations."""
    
    def setUp(self):
        """Set up test data."""
        self.dept = Department.objects.create(name='Sales')
        self.dept_eng = Department.objects.create(name='Engineering')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.admin_user, role='admin')
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.manager_user, role='manager', department=self.dept)
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.employee_user, role='employee', department=self.dept)
        
        self.client = APIClient()
    
    def test_list_users_admin_only(self):
        """Test that only admins can list all users."""
        # Admin should be able to list users
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/user-management/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)
    
    def test_list_users_non_admin_denied(self):
        """Test that non-admins cannot list all users."""
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/user-management/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_user_with_all_fields(self):
        """Test creating a new user with all fields."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'employee',
            'department_id': self.dept.id,
            'manager_id': self.manager_user.id
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        
        # Verify profile was created
        profile = user.profile
        self.assertEqual(profile.role, 'employee')
        self.assertEqual(profile.department, self.dept)
        self.assertEqual(profile.manager, self.manager_user)
    
    def test_create_user_minimal_fields(self):
        """Test creating a new user with minimal fields."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'minimaluser',
            'email': 'minimal@test.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='minimaluser')
        profile = user.profile
        self.assertEqual(profile.role, 'employee')  # Default role
        self.assertIsNone(profile.department)
        self.assertIsNone(profile.manager)
    
    def test_create_user_duplicate_username(self):
        """Test that duplicate usernames are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'employee',  # Already exists
            'email': 'newemail@test.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error'].lower())
    
    def test_create_user_duplicate_email(self):
        """Test that duplicate emails are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'employee@test.com',  # Already exists
            'password': 'testpass123'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error'].lower())
    
    def test_create_user_invalid_email(self):
        """Test that invalid emails are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_user_short_password(self):
        """Test that short passwords are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'short'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_user_invalid_department(self):
        """Test that invalid department is rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'department_id': 9999
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Department not found', response.data['error'])
    
    def test_create_user_invalid_manager(self):
        """Test that invalid manager is rejected."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'manager_id': 9999
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Manager not found', response.data['error'])
    
    def test_retrieve_user(self):
        """Test retrieving a specific user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/user-management/{self.employee_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'employee')
    
    def test_retrieve_nonexistent_user(self):
        """Test retrieving a nonexistent user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/user-management/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_user_role(self):
        """Test updating user role."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'role': 'manager'}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.role, 'manager')
    
    def test_update_user_manager(self):
        """Test updating user manager assignment."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'manager_id': self.manager_user.id}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.manager, self.manager_user)
    
    def test_update_user_department(self):
        """Test updating user department."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'department_id': self.dept_eng.id}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.department, self.dept_eng)
    
    def test_update_user_multiple_fields(self):
        """Test updating multiple user fields."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'role': 'manager',
            'department_id': self.dept_eng.id,
            'manager_id': self.manager_user.id
        }
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertEqual(self.employee_user.profile.role, 'manager')
        self.assertEqual(self.employee_user.profile.department, self.dept_eng)
        self.assertEqual(self.employee_user.profile.manager, self.manager_user)
    
    def test_update_user_invalid_manager(self):
        """Test that invalid manager is rejected on update."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'manager_id': 9999}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_user_invalid_department(self):
        """Test that invalid department is rejected on update."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'department_id': 9999}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/user-management/{self.employee_user.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertFalse(self.employee_user.profile.is_active)
    
    def test_deactivate_already_inactive_user(self):
        """Test deactivating an already inactive user."""
        self.employee_user.profile.is_active = False
        self.employee_user.profile.save()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/user-management/{self.employee_user.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reactivate_user(self):
        """Test reactivating a user."""
        self.employee_user.profile.is_active = False
        self.employee_user.profile.save()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/user-management/{self.employee_user.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.employee_user.profile.refresh_from_db()
        self.assertTrue(self.employee_user.profile.is_active)
    
    def test_reactivate_already_active_user(self):
        """Test reactivating an already active user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/user-management/{self.employee_user.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_user_non_admin_denied(self):
        """Test that non-admins cannot create users."""
        self.client.force_authenticate(user=self.employee_user)
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_user_non_admin_denied(self):
        """Test that non-admins cannot update users."""
        self.client.force_authenticate(user=self.employee_user)
        data = {'role': 'manager'}
        response = self.client.put(f'/api/user-management/{self.manager_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_deactivate_user_non_admin_denied(self):
        """Test that non-admins cannot deactivate users."""
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/user-management/{self.manager_user.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_audit_trail_on_user_creation(self):
        """Test that audit trail is created on user creation."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'audituser',
            'email': 'audit@test.com',
            'password': 'testpass123',
            'role': 'employee'
        }
        response = self.client.post('/api/user-management/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check audit log
        user = User.objects.get(username='audituser')
        audit_logs = AuditLog.objects.filter(entity_type='user', entity_id=user.id, action='create')
        self.assertEqual(audit_logs.count(), 1)
        self.assertEqual(audit_logs.first().user, self.admin_user)
    
    def test_audit_trail_on_user_update(self):
        """Test that audit trail is created on user update."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'role': 'manager'}
        response = self.client.put(f'/api/user-management/{self.employee_user.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check audit log
        audit_logs = AuditLog.objects.filter(
            entity_type='user',
            entity_id=self.employee_user.id,
            action='update'
        )
        self.assertGreater(audit_logs.count(), 0)
    
    def test_audit_trail_on_user_deactivation(self):
        """Test that audit trail is created on user deactivation."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/user-management/{self.employee_user.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check audit log
        audit_logs = AuditLog.objects.filter(
            entity_type='user',
            entity_id=self.employee_user.id,
            action='update'
        )
        self.assertGreater(audit_logs.count(), 0)
        latest_log = audit_logs.latest('created_at')
        self.assertEqual(latest_log.new_values['is_active'], False)


# ============================================================================
# Phase 3: Validation Engine Tests
# ============================================================================

class ValidationEngineTestCase(TestCase):
    """Test cases for validation engine."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.cycle = Cycle.objects.create(
            name='FY2024',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
        self.uom_numeric, _ = UoMType.objects.get_or_create(name='numeric')
    
    def test_weightage_validation_equals_100(self):
        """Test weightage validation when total equals 100%."""
        goals = [
            Goal(weightage=50),
            Goal(weightage=50)
        ]
        is_valid, total = validate_weightage(goals)
        self.assertTrue(is_valid)
        self.assertEqual(total, 100)
    
    def test_weightage_validation_not_100(self):
        """Test weightage validation when total doesn't equal 100%."""
        goals = [
            Goal(weightage=50),
            Goal(weightage=40)
        ]
        is_valid, total = validate_weightage(goals)
        self.assertFalse(is_valid)
        self.assertEqual(total, 90)
    
    def test_goal_count_constraint(self):
        """Test goal count constraint (max 8 per cycle)."""
        # Create 8 goals
        for i in range(8):
            Goal.objects.create(
                user=self.user,
                cycle=self.cycle,
                title=f'Goal {i}',
                target_value=100,
                weightage=12.5,
                thrust_area=self.thrust_area,
                uom_type=self.uom_numeric
            )
        
        is_valid, count, max_count = validate_goal_count(self.user, self.cycle)
        self.assertFalse(is_valid)
        self.assertEqual(count, 8)
        self.assertEqual(max_count, 8)
    
    def test_goal_count_below_limit(self):
        """Test goal count when below limit."""
        Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Goal 1',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_numeric
        )
        
        is_valid, count, max_count = validate_goal_count(self.user, self.cycle)
        self.assertTrue(is_valid)
        self.assertEqual(count, 1)


# ============================================================================
# Phase 4: Goal Management Tests
# ============================================================================

class GoalManagementTestCase(APITestCase):
    """Test cases for goal management."""
    
    def setUp(self):
        """Set up test data."""
        self.dept = Department.objects.create(name='Sales')
        
        self.user = User.objects.create_user(username='employee', password='pass')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='employee',
            department=self.dept
        )
        
        self.manager = User.objects.create_user(username='manager', password='pass')
        self.manager_profile = UserProfile.objects.create(
            user=self.manager,
            role='manager',
            department=self.dept
        )
        self.user_profile.manager = self.manager
        self.user_profile.save()
        
        self.cycle = Cycle.objects.create(
            name='FY2024',
            status='active',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
        self.uom_numeric, _ = UoMType.objects.get_or_create(name='numeric')
        
        self.client = APIClient()
    
    def test_create_goal(self):
        """Test creating a goal."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Increase Sales',
            'description': 'Increase sales by 20%',
            'cycle': self.cycle.id,
            'thrust_area': self.thrust_area.id,
            'uom_type': self.uom_numeric.id,
            'target_value': 1000000,
            'weightage': 50
        }
        response = self.client.post('/api/goals/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Goal.objects.filter(title='Increase Sales').exists())
    
    def test_create_goal_exceeds_max_count(self):
        """Test that creating more than 8 goals is rejected."""
        self.client.force_authenticate(user=self.user)
        
        # Create 8 goals
        for i in range(8):
            Goal.objects.create(
                user=self.user,
                cycle=self.cycle,
                title=f'Goal {i}',
                target_value=100,
                weightage=12.5,
                thrust_area=self.thrust_area,
                uom_type=self.uom_numeric
            )
        
        # Try to create 9th goal
        data = {
            'title': 'Goal 9',
            'cycle': self.cycle.id,
            'target_value': 100,
            'weightage': 12.5
        }
        response = self.client.post('/api/goals/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_goal(self):
        """Test submitting a goal for approval."""
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=self.uom_numeric,
            status='draft'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/goals/{goal.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'submitted')
    
    def test_approve_goal(self):
        """Test approving a goal."""
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=self.uom_numeric,
            status='submitted'
        )
        
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'approved')
        self.assertEqual(goal.approved_by, self.manager)
    
    def test_reject_goal(self):
        """Test rejecting a goal."""
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=self.uom_numeric,
            status='submitted'
        )
        
        self.client.force_authenticate(user=self.manager)
        data = {'rejection_reason': 'Target too high'}
        response = self.client.post(f'/api/goals/{goal.id}/reject/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertEqual(goal.status, 'rejected')


# ============================================================================
# Phase 3: Progress Scoring Tests
# ============================================================================

class ProgressScoringTestCase(TestCase):
    """Test cases for progress scoring engine."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.cycle = Cycle.objects.create(
            name='FY2024',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
    
    def test_numeric_progress_scoring(self):
        """Test progress scoring for Numeric UoM."""
        uom, _ = UoMType.objects.get_or_create(name='numeric')
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Sales Goal',
            target_value=1000,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=uom
        )
        
        # Test 50% progress
        progress = calculate_progress_percentage(goal, 500)
        self.assertEqual(progress, 50)
        
        # Test 100% progress
        progress = calculate_progress_percentage(goal, 1000)
        self.assertEqual(progress, 100)
        
        # Test over 100% (should cap at 100)
        progress = calculate_progress_percentage(goal, 1500)
        self.assertEqual(progress, 100)
    
    def test_percentage_progress_scoring(self):
        """Test progress scoring for Percentage UoM."""
        uom, _ = UoMType.objects.get_or_create(name='percentage')
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Satisfaction Goal',
            target_value=100,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=uom
        )
        
        # Test direct mapping
        progress = calculate_progress_percentage(goal, 75)
        self.assertEqual(progress, 75)
    
    def test_zero_based_progress_scoring(self):
        """Test progress scoring for Zero-based UoM."""
        uom, _ = UoMType.objects.get_or_create(name='zero_based')
        goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Completion Goal',
            target_value=1,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=uom
        )
        
        # Test 0% progress (zero value)
        progress = calculate_progress_percentage(goal, 0)
        self.assertEqual(progress, 0)
        
        # Test 100% progress (non-zero value)
        progress = calculate_progress_percentage(goal, 1)
        self.assertEqual(progress, 100)


# ============================================================================
# Phase 8: Check-in Tests
# ============================================================================

class CheckInTestCase(APITestCase):
    """Test cases for check-in management."""
    
    def setUp(self):
        """Set up test data."""
        self.dept = Department.objects.create(name='Sales')
        
        self.user = User.objects.create_user(username='employee', password='pass')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='employee',
            department=self.dept
        )
        
        self.manager = User.objects.create_user(username='manager', password='pass')
        self.manager_profile = UserProfile.objects.create(
            user=self.manager,
            role='manager',
            department=self.dept
        )
        
        self.cycle = Cycle.objects.create(
            name='FY2024',
            status='active',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date()
        )
        self.cycle.set_checkin_dates()
        self.cycle.save()
        
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue')
        self.uom_numeric, _ = UoMType.objects.get_or_create(name='numeric')
        
        self.goal = Goal.objects.create(
            user=self.user,
            cycle=self.cycle,
            title='Sales Goal',
            target_value=1000,
            weightage=100,
            thrust_area=self.thrust_area,
            uom_type=self.uom_numeric,
            status='approved'
        )
        
        self.client = APIClient()
    
    def test_checkin_period_validation(self):
        """Test check-in period validation."""
        # Set check-in date to today
        today = timezone.now().date()
        self.cycle.checkin_date_q1 = today
        self.cycle.save()
        
        is_active, next_date, period = validate_checkin_period(self.cycle, today)
        self.assertTrue(is_active)
        self.assertEqual(period, 'Q1')
    
    def test_checkin_period_inactive(self):
        """Test check-in period when inactive."""
        # Set check-in date to future
        future_date = timezone.now().date() + timedelta(days=30)
        self.cycle.checkin_date_q1 = future_date
        self.cycle.save()
        
        is_active, next_date, period = validate_checkin_period(self.cycle)
        self.assertFalse(is_active)


# ============================================================================
# Phase 9: Audit Trail Tests
# ============================================================================

class AuditTrailTestCase(TestCase):
    """Test cases for audit trail logging."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='pass')
    
    def test_audit_log_creation(self):
        """Test that audit logs are created."""
        from .utils import log_audit_trail
        
        log_audit_trail(
            entity_type='goal',
            entity_id=1,
            action='create',
            user=self.user,
            new_values={'title': 'Test Goal'}
        )
        
        log = AuditLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.entity_type, 'goal')
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.user, self.user)


# ============================================================================
# Weighted Achievement Tests
# ============================================================================

class WeightedAchievementTestCase(TestCase):
    """Test cases for weighted achievement calculation."""
    
    def test_weighted_achievement_calculation(self):
        """Test weighted achievement score calculation."""
        from .models import Goal
        
        goals_with_progress = [
            (Goal(weightage=50), 80),  # 50% weight, 80% progress
            (Goal(weightage=50), 60),  # 50% weight, 60% progress
        ]
        
        achievement = calculate_weighted_achievement(goals_with_progress)
        expected = ((0.8 * 50) + (0.6 * 50)) / 100 * 100
        self.assertEqual(achievement, expected)
    
    def test_weighted_achievement_empty(self):
        """Test weighted achievement with no goals."""
        achievement = calculate_weighted_achievement([])
        self.assertEqual(achievement, 0)
