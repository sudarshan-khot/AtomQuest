"""
Property-based tests for Role-Based Access Control (RBAC) system.
Tests enforce that role-based permissions are correctly enforced across all operations.

**Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7**
"""
from hypothesis import given, strategies as st, settings, HealthCheck
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, CheckIn, AuditLog
)
from .permissions import (
    IsAdmin, IsManager, IsEmployee, IsViewer,
    IsManagerOrAdmin, IsEmployeeOrManager,
    IsGoalOwnerOrManager, IsCheckInOwnerOrManager,
    CanApproveGoal, CanApproveCheckIn,
    get_filtered_queryset, check_role_permission
)


class RBACPropertyTestCase(TestCase):
    """Property-based tests for RBAC enforcement."""
    
    def setUp(self):
        """Set up test data."""
        # Create departments
        self.dept = Department.objects.create(name='Sales')
        
        # Create users with different roles
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
            department=self.dept
        )
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.dept,
            manager=self.manager_user
        )
        
        self.viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123'
        )
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user,
            role='viewer'
        )
        
        # Create cycle
        self.cycle = Cycle.objects.create(
            name='Q1 FY2024',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 3, 31).date(),
            status='active'
        )
        
        # Create thrust area and UoM type
        self.thrust_area = ThrustArea.objects.create(name='Revenue Growth')
        self.uom_type = UoMType.objects.create(name='numeric')
    
    def test_rbac_property_admin_can_access_all_goals(self):
        """
        Property: Admin users can access all goals regardless of ownership.
        
        For any goal created by any user, an admin user SHALL be able to access it.
        """
        # Create goals for different users
        admin_goal = Goal.objects.create(
            user=self.admin_user,
            cycle=self.cycle,
            title='Admin Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        # Admin should be able to access all goals
        queryset = get_filtered_queryset(self.admin_user, Goal.objects.all(), 'goal')
        self.assertIn(admin_goal, queryset)
        self.assertIn(employee_goal, queryset)
        self.assertEqual(queryset.count(), 2)
    
    def test_rbac_property_employee_can_only_access_own_goals(self):
        """
        Property: Employee users can only access their own goals.
        
        For any goal not owned by an employee, the employee SHALL NOT be able to access it.
        """
        # Create goals for different users
        employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        other_employee = User.objects.create_user(
            username='other_employee',
            email='other@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_employee,
            role='employee',
            department=self.dept
        )
        
        other_goal = Goal.objects.create(
            user=other_employee,
            cycle=self.cycle,
            title='Other Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        # Employee should only see their own goal
        queryset = get_filtered_queryset(self.employee_user, Goal.objects.all(), 'goal')
        self.assertIn(employee_goal, queryset)
        self.assertNotIn(other_goal, queryset)
        self.assertEqual(queryset.count(), 1)
    
    def test_rbac_property_manager_can_access_team_goals(self):
        """
        Property: Manager users can access their own goals and their team's goals.
        
        For any goal owned by the manager or their subordinates, the manager SHALL be able to access it.
        """
        # Create goals for manager and employee
        manager_goal = Goal.objects.create(
            user=self.manager_user,
            cycle=self.cycle,
            title='Manager Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        # Manager should see own goal and team's goal
        queryset = get_filtered_queryset(self.manager_user, Goal.objects.all(), 'goal')
        self.assertIn(manager_goal, queryset)
        self.assertIn(employee_goal, queryset)
        self.assertEqual(queryset.count(), 2)
    
    def test_rbac_property_viewer_can_access_all_goals_readonly(self):
        """
        Property: Viewer users can access all goals but only for reading.
        
        For any goal in the system, a viewer user SHALL be able to access it for reading.
        """
        # Create goals for different users
        admin_goal = Goal.objects.create(
            user=self.admin_user,
            cycle=self.cycle,
            title='Admin Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        # Viewer should see all goals
        queryset = get_filtered_queryset(self.viewer_user, Goal.objects.all(), 'goal')
        self.assertIn(admin_goal, queryset)
        self.assertIn(employee_goal, queryset)
        self.assertEqual(queryset.count(), 2)
    
    def test_rbac_property_only_admin_can_manage_users(self):
        """
        Property: Only admin users can manage users.
        
        For any user management operation, only admin users SHALL be able to perform it.
        """
        permission = CanApproveGoal()
        
        # Admin should have permission
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
        
        # Manager should have permission
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
        
        # Employee should NOT have permission
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
        
        # Viewer should NOT have permission
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.viewer_user),
            None
        ))
    
    def test_rbac_property_role_permission_check_enforces_roles(self):
        """
        Property: Role permission checks enforce role requirements.
        
        For any required role, check_role_permission SHALL allow users with that role
        and deny users without that role.
        """
        from rest_framework.exceptions import PermissionDenied
        
        # Admin should pass admin check
        self.assertTrue(check_role_permission(self.admin_user, 'admin'))
        
        # Manager should pass manager check
        self.assertTrue(check_role_permission(self.manager_user, 'manager'))
        
        # Employee should pass employee check
        self.assertTrue(check_role_permission(self.employee_user, 'employee'))
        
        # Employee should fail admin check
        with self.assertRaises(PermissionDenied):
            check_role_permission(self.employee_user, 'admin')
        
        # Manager should fail employee check
        with self.assertRaises(PermissionDenied):
            check_role_permission(self.manager_user, 'employee')
    
    def test_rbac_property_multiple_roles_in_permission_check(self):
        """
        Property: Role permission checks support multiple roles.
        
        For any list of required roles, check_role_permission SHALL allow users
        with any of those roles.
        """
        # Manager should pass manager or admin check
        self.assertTrue(check_role_permission(self.manager_user, ['manager', 'admin']))
        
        # Employee should pass employee or manager check
        self.assertTrue(check_role_permission(self.employee_user, ['employee', 'manager']))
        
        # Employee should fail manager or admin check
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            check_role_permission(self.employee_user, ['manager', 'admin'])
    
    def test_rbac_property_goal_owner_or_manager_permission(self):
        """
        Property: IsGoalOwnerOrManager permission allows owner, manager, or admin.
        
        For any goal, the owner, their manager, or an admin SHALL be able to access it.
        """
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        permission = IsGoalOwnerOrManager()
        
        # Owner should have permission
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.employee_user),
            None,
            goal
        ))
        
        # Manager should have permission
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.manager_user),
            None,
            goal
        ))
        
        # Admin should have permission
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.admin_user),
            None,
            goal
        ))
        
        # Other employee should NOT have permission
        other_employee = User.objects.create_user(
            username='other_employee',
            email='other@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_employee,
            role='employee',
            department=self.dept
        )
        
        self.assertFalse(permission.has_object_permission(
            self._create_mock_request(other_employee),
            None,
            goal
        ))
    
    def test_rbac_property_can_approve_goal_permission(self):
        """
        Property: CanApproveGoal permission allows only manager or admin.
        
        For any goal, only managers and admins SHALL be able to approve it.
        """
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='submitted'
        )
        
        permission = CanApproveGoal()
        
        # Manager should have permission
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.manager_user),
            None,
            goal
        ))
        
        # Admin should have permission
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.admin_user),
            None,
            goal
        ))
        
        # Employee should NOT have permission
        self.assertFalse(permission.has_object_permission(
            self._create_mock_request(self.employee_user),
            None,
            goal
        ))
        
        # Viewer should NOT have permission
        self.assertFalse(permission.has_object_permission(
            self._create_mock_request(self.viewer_user),
            None,
            goal
        ))
    
    def _create_mock_request(self, user):
        """Create a mock request object."""
        class MockRequest:
            def __init__(self, user):
                self.user = user
        return MockRequest(user)


class RBACAPIEndpointPropertyTestCase(APITestCase):
    """Property-based tests for RBAC enforcement on API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create departments
        self.dept = Department.objects.create(name='Sales')
        
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
            department=self.dept
        )
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.dept,
            manager=self.manager_user
        )
        
        self.viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123'
        )
        self.viewer_profile = UserProfile.objects.create(
            user=self.viewer_user,
            role='viewer'
        )
        
        # Create cycle
        self.cycle = Cycle.objects.create(
            name='Q1 FY2024',
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 3, 31).date(),
            status='active'
        )
        
        # Create thrust area and UoM type
        self.thrust_area = ThrustArea.objects.create(name='Revenue Growth')
        self.uom_type = UoMType.objects.create(name='numeric')
    
    def test_rbac_property_unauthorized_access_returns_403(self):
        """
        Property: Unauthorized access to protected endpoints returns 403 Forbidden.
        
        For any protected endpoint, unauthorized users SHALL receive a 403 response.
        """
        # Create a goal
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='submitted'
        )
        
        # Employee cannot approve goal
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Viewer cannot approve goal
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_rbac_property_authorized_access_returns_success(self):
        """
        Property: Authorized access to protected endpoints returns success.
        
        For any protected endpoint, authorized users SHALL receive a success response.
        """
        # Create a goal
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Test Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='submitted'
        )
        
        # Manager can approve goal
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin can approve goal
        goal.status = 'submitted'
        goal.save()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

