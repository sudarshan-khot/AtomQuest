"""
Comprehensive tests for Role-Based Access Control (RBAC) system.
Tests enforce role-based permissions for all operations.
"""
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


class RBACPermissionClassesTestCase(TestCase):
    """Test individual permission classes."""
    
    def setUp(self):
        """Set up test data."""
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
            role='manager'
        )
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee'
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
    
    def test_is_admin_permission_allows_admin(self):
        """Test IsAdmin permission allows admin users."""
        permission = IsAdmin()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
    
    def test_is_admin_permission_denies_non_admin(self):
        """Test IsAdmin permission denies non-admin users."""
        permission = IsAdmin()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
    
    def test_is_manager_permission_allows_manager(self):
        """Test IsManager permission allows manager users."""
        permission = IsManager()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
    
    def test_is_manager_permission_denies_non_manager(self):
        """Test IsManager permission denies non-manager users."""
        permission = IsManager()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
    
    def test_is_employee_permission_allows_employee(self):
        """Test IsEmployee permission allows employee users."""
        permission = IsEmployee()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
    
    def test_is_employee_permission_denies_non_employee(self):
        """Test IsEmployee permission denies non-employee users."""
        permission = IsEmployee()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
    
    def test_is_viewer_permission_allows_viewer(self):
        """Test IsViewer permission allows viewer users."""
        permission = IsViewer()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.viewer_user),
            None
        ))
    
    def test_is_viewer_permission_denies_non_viewer(self):
        """Test IsViewer permission denies non-viewer users."""
        permission = IsViewer()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
    
    def test_is_manager_or_admin_permission_allows_manager(self):
        """Test IsManagerOrAdmin permission allows manager users."""
        permission = IsManagerOrAdmin()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
    
    def test_is_manager_or_admin_permission_allows_admin(self):
        """Test IsManagerOrAdmin permission allows admin users."""
        permission = IsManagerOrAdmin()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
    
    def test_is_manager_or_admin_permission_denies_employee(self):
        """Test IsManagerOrAdmin permission denies employee users."""
        permission = IsManagerOrAdmin()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
    
    def test_is_employee_or_manager_permission_allows_employee(self):
        """Test IsEmployeeOrManager permission allows employee users."""
        permission = IsEmployeeOrManager()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.employee_user),
            None
        ))
    
    def test_is_employee_or_manager_permission_allows_manager(self):
        """Test IsEmployeeOrManager permission allows manager users."""
        permission = IsEmployeeOrManager()
        self.assertTrue(permission.has_permission(
            self._create_mock_request(self.manager_user),
            None
        ))
    
    def test_is_employee_or_manager_permission_denies_admin(self):
        """Test IsEmployeeOrManager permission denies admin users."""
        permission = IsEmployeeOrManager()
        self.assertFalse(permission.has_permission(
            self._create_mock_request(self.admin_user),
            None
        ))
    
    def _create_mock_request(self, user):
        """Create a mock request object."""
        class MockRequest:
            def __init__(self, user):
                self.user = user
        return MockRequest(user)


class RBACObjectPermissionsTestCase(TestCase):
    """Test object-level permission classes."""
    
    def setUp(self):
        """Set up test data."""
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
        
        self.other_employee_user = User.objects.create_user(
            username='other_employee',
            email='other@test.com',
            password='testpass123'
        )
        self.other_employee_profile = UserProfile.objects.create(
            user=self.other_employee_user,
            role='employee',
            department=self.dept
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
        
        # Create goals
        self.employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        self.other_employee_goal = Goal.objects.create(
            user=self.other_employee_user,
            cycle=self.cycle,
            title='Other Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
    
    def test_is_goal_owner_or_manager_allows_owner(self):
        """Test IsGoalOwnerOrManager allows goal owner."""
        permission = IsGoalOwnerOrManager()
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.employee_user),
            None,
            self.employee_goal
        ))
    
    def test_is_goal_owner_or_manager_allows_manager(self):
        """Test IsGoalOwnerOrManager allows manager of goal owner."""
        permission = IsGoalOwnerOrManager()
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.manager_user),
            None,
            self.employee_goal
        ))
    
    def test_is_goal_owner_or_manager_allows_admin(self):
        """Test IsGoalOwnerOrManager allows admin."""
        permission = IsGoalOwnerOrManager()
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.admin_user),
            None,
            self.employee_goal
        ))
    
    def test_is_goal_owner_or_manager_denies_other_employee(self):
        """Test IsGoalOwnerOrManager denies other employees."""
        permission = IsGoalOwnerOrManager()
        self.assertFalse(permission.has_object_permission(
            self._create_mock_request(self.other_employee_user),
            None,
            self.employee_goal
        ))
    
    def test_can_approve_goal_allows_manager(self):
        """Test CanApproveGoal allows manager."""
        permission = CanApproveGoal()
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.manager_user),
            None,
            self.employee_goal
        ))
    
    def test_can_approve_goal_allows_admin(self):
        """Test CanApproveGoal allows admin."""
        permission = CanApproveGoal()
        self.assertTrue(permission.has_object_permission(
            self._create_mock_request(self.admin_user),
            None,
            self.employee_goal
        ))
    
    def test_can_approve_goal_denies_employee(self):
        """Test CanApproveGoal denies employee."""
        permission = CanApproveGoal()
        self.assertFalse(permission.has_object_permission(
            self._create_mock_request(self.employee_user),
            None,
            self.employee_goal
        ))
    
    def _create_mock_request(self, user):
        """Create a mock request object."""
        class MockRequest:
            def __init__(self, user):
                self.user = user
        return MockRequest(user)


class RBACFilteringTestCase(TestCase):
    """Test role-based filtering for list endpoints."""
    
    def setUp(self):
        """Set up test data."""
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
        
        self.other_employee_user = User.objects.create_user(
            username='other_employee',
            email='other@test.com',
            password='testpass123'
        )
        self.other_employee_profile = UserProfile.objects.create(
            user=self.other_employee_user,
            role='employee',
            department=self.dept
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
        
        # Create goals for different users
        self.admin_goal = Goal.objects.create(
            user=self.admin_user,
            cycle=self.cycle,
            title='Admin Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        self.manager_goal = Goal.objects.create(
            user=self.manager_user,
            cycle=self.cycle,
            title='Manager Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        self.employee_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title='Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        self.other_employee_goal = Goal.objects.create(
            user=self.other_employee_user,
            cycle=self.cycle,
            title='Other Employee Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
    
    def test_admin_sees_all_goals(self):
        """Test admin can see all goals."""
        queryset = get_filtered_queryset(self.admin_user, Goal.objects.all(), 'goal')
        self.assertEqual(queryset.count(), 4)
    
    def test_manager_sees_own_and_team_goals(self):
        """Test manager can see own goals and team's goals."""
        queryset = get_filtered_queryset(self.manager_user, Goal.objects.all(), 'goal')
        self.assertEqual(queryset.count(), 3)  # Manager goal + 2 employee goals
        self.assertIn(self.manager_goal, queryset)
        self.assertIn(self.employee_goal, queryset)
        self.assertIn(self.other_employee_goal, queryset)
    
    def test_employee_sees_only_own_goals(self):
        """Test employee can only see own goals."""
        queryset = get_filtered_queryset(self.employee_user, Goal.objects.all(), 'goal')
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.employee_goal, queryset)
    
    def test_viewer_sees_all_goals(self):
        """Test viewer can see all goals (read-only)."""
        viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123'
        )
        viewer_profile = UserProfile.objects.create(
            user=viewer_user,
            role='viewer'
        )
        queryset = get_filtered_queryset(viewer_user, Goal.objects.all(), 'goal')
        self.assertEqual(queryset.count(), 4)


class RBACAPIEndpointsTestCase(APITestCase):
    """Test RBAC enforcement on API endpoints."""
    
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
    
    def test_employee_cannot_approve_goal(self):
        """Test employee cannot approve goals."""
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
        
        # Try to approve as employee
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_can_approve_team_goal(self):
        """Test manager can approve team member's goal."""
        # Create a goal for employee
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
        
        # Approve as manager
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_approve_any_goal(self):
        """Test admin can approve any goal."""
        # Create a goal for employee
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
        
        # Approve as admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/goals/{goal.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_employee_cannot_access_other_employee_goals(self):
        """Test employee cannot access other employee's goals."""
        # Create another employee
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
        
        # Create goal for other employee
        goal = Goal.objects.create(
            user=other_employee,
            cycle=self.cycle,
            title='Other Goal',
            target_value=100,
            weightage=50,
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            status='draft'
        )
        
        # Try to access as different employee
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f'/api/goals/{goal.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_manager_can_access_team_goals(self):
        """Test manager can access team member's goals."""
        # Create goal for employee
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
        
        # Access as manager
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(f'/api/goals/{goal.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RBACCheckRolePermissionTestCase(TestCase):
    """Test check_role_permission utility function."""
    
    def setUp(self):
        """Set up test data."""
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
            role='manager'
        )
    
    def test_check_role_permission_allows_matching_role(self):
        """Test check_role_permission allows matching role."""
        result = check_role_permission(self.admin_user, 'admin')
        self.assertTrue(result)
    
    def test_check_role_permission_denies_non_matching_role(self):
        """Test check_role_permission denies non-matching role."""
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            check_role_permission(self.admin_user, 'manager')
    
    def test_check_role_permission_allows_multiple_roles(self):
        """Test check_role_permission allows multiple roles."""
        result = check_role_permission(self.manager_user, ['admin', 'manager'])
        self.assertTrue(result)
    
    def test_check_role_permission_denies_unauthenticated(self):
        """Test check_role_permission denies unauthenticated users."""
        from rest_framework.exceptions import PermissionDenied
        unauthenticated_user = User()
        unauthenticated_user.is_authenticated = False
        with self.assertRaises(PermissionDenied):
            check_role_permission(unauthenticated_user, 'admin')
