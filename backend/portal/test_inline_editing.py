"""
Tests for inline editing during goal approval review.

This test module covers:
1. Inline editing endpoint functionality
2. Permission validation (only managers/admins can edit)
3. Status validation (only submitted goals can be edited)
4. Shared goal readonly field protection
5. Audit trail logging for inline edits
6. Field validation during inline editing
7. Notification sending on inline edits
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle,
    Goal, AuditLog, Notification
)


class InlineEditingPermissionTests(APITestCase):
    """Test permission validation for inline editing."""
    
    def setUp(self):
        """Set up test data."""
        # Create department
        self.department = Department.objects.create(name="Engineering")
        
        # Create users
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department,
            manager=None
        )
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='admin'
        )
        
        # Create cycle
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        # Create thrust area and UoM type
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        # Create a submitted goal
        self.goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Increase Sales",
            description="Increase sales by 20%",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        self.client = APIClient()
    
    def test_manager_can_edit_submitted_goal(self):
        """Test that managers can edit submitted goals."""
        self.client.force_authenticate(user=self.manager_user)
        
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {
            'title': 'Updated Sales Goal',
            'target_value': 150000
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Sales Goal'
        assert response.data['target_value'] == 150000
    
    def test_admin_can_edit_submitted_goal(self):
        """Test that admins can edit submitted goals."""
        self.client.force_authenticate(user=self.admin_user)
        
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {
            'title': 'Updated by Admin',
            'weightage': 60
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated by Admin'
        assert response.data['weightage'] == 60
    
    def test_employee_cannot_edit_submitted_goal(self):
        """Test that employees cannot edit submitted goals."""
        self.client.force_authenticate(user=self.employee_user)
        
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {'title': 'Hacked Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_unauthenticated_user_cannot_edit(self):
        """Test that unauthenticated users cannot edit goals."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {'title': 'Hacked Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class InlineEditingStatusValidationTests(APITestCase):
    """Test status validation for inline editing."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)
    
    def test_cannot_edit_draft_goal(self):
        """Test that draft goals cannot be edited via inline editing endpoint."""
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Draft Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='draft'
        )
        
        url = f'/api/goals/{goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'submitted status' in response.data['error'].lower()
    
    def test_cannot_edit_approved_goal(self):
        """Test that approved goals cannot be edited via inline editing endpoint."""
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Approved Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='approved',
            approved_by=self.manager_user,
            approved_at=datetime.now()
        )
        
        url = f'/api/goals/{goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'submitted status' in response.data['error'].lower()
    
    def test_cannot_edit_rejected_goal(self):
        """Test that rejected goals cannot be edited via inline editing endpoint."""
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Rejected Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='rejected'
        )
        
        url = f'/api/goals/{goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'submitted status' in response.data['error'].lower()
    
    def test_can_edit_submitted_goal(self):
        """Test that submitted goals can be edited."""
        goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Submitted Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        url = f'/api/goals/{goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'


class InlineEditingFieldValidationTests(APITestCase):
    """Test field validation during inline editing."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        self.goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Test Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)
    
    def test_edit_title_validation(self):
        """Test that title is validated during inline editing."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        
        # Empty title should fail
        data = {'title': ''}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Valid title should succeed
        data = {'title': 'New Valid Title'}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_edit_weightage_validation(self):
        """Test that weightage is validated during inline editing."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        
        # Weightage below 10 should fail
        data = {'weightage': 5}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Weightage above 100 should fail
        data = {'weightage': 150}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Valid weightage should succeed
        data = {'weightage': 75}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_edit_target_value_validation(self):
        """Test that target value is validated during inline editing."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        
        # Negative target should fail
        data = {'target_value': -100}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Valid target should succeed
        data = {'target_value': 200000}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
    
    def test_edit_description_validation(self):
        """Test that description is validated during inline editing."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        
        # Very long description should fail
        long_desc = 'x' * 2001
        data = {'description': long_desc}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Valid description should succeed
        data = {'description': 'Updated description'}
        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK


class InlineEditingSharedGoalTests(APITestCase):
    """Test inline editing with shared goals."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        # Create a shared goal
        self.shared_goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Shared KPI",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted',
            is_shared=True,
            is_readonly_title=True,
            is_readonly_target=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)
    
    def test_cannot_edit_shared_goal_title(self):
        """Test that shared goal title cannot be edited."""
        url = f'/api/goals/{self.shared_goal.id}/edit_during_review/'
        data = {'title': 'New Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'read-only' in response.data['error'].lower()
    
    def test_cannot_edit_shared_goal_target(self):
        """Test that shared goal target cannot be edited."""
        url = f'/api/goals/{self.shared_goal.id}/edit_during_review/'
        data = {'target_value': 200000}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'read-only' in response.data['error'].lower()
    
    def test_can_edit_shared_goal_weightage(self):
        """Test that shared goal weightage can be edited."""
        url = f'/api/goals/{self.shared_goal.id}/edit_during_review/'
        data = {'weightage': 60}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weightage'] == 60


class InlineEditingAuditTrailTests(APITestCase):
    """Test audit trail logging for inline edits."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        self.goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Test Goal",
            description="Original description",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)
    
    def test_audit_trail_created_for_inline_edit(self):
        """Test that audit trail entry is created for inline edits."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {
            'title': 'Updated Title',
            'target_value': 150000
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check audit log was created
        audit_logs = AuditLog.objects.filter(
            entity_type='goal',
            entity_id=self.goal.id,
            action='update'
        )
        
        assert audit_logs.exists()
        audit_log = audit_logs.latest('created_at')
        
        # Verify audit log contains old and new values
        assert audit_log.old_values['title'] == 'Test Goal'
        assert audit_log.new_values['title'] == 'Updated Title'
        assert audit_log.old_values['target_value'] == 100000
        assert audit_log.new_values['target_value'] == 150000
        assert audit_log.user == self.manager_user
        assert 'inline edit' in audit_log.comments.lower()
    
    def test_audit_trail_contains_manager_info(self):
        """Test that audit trail contains manager information."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {'title': 'Updated by Manager'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        audit_log = AuditLog.objects.filter(
            entity_type='goal',
            entity_id=self.goal.id,
            action='update'
        ).latest('created_at')
        
        assert audit_log.user == self.manager_user
        assert self.manager_user.username in audit_log.comments
    
    def test_multiple_edits_create_multiple_audit_logs(self):
        """Test that multiple edits create separate audit log entries."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        
        # First edit
        response1 = self.client.patch(url, {'title': 'First Update'}, format='json')
        assert response1.status_code == status.HTTP_200_OK
        
        # Second edit
        response2 = self.client.patch(url, {'weightage': 60}, format='json')
        assert response2.status_code == status.HTTP_200_OK
        
        # Check both audit logs exist
        audit_logs = AuditLog.objects.filter(
            entity_type='goal',
            entity_id=self.goal.id,
            action='update'
        ).order_by('created_at')
        
        assert audit_logs.count() >= 2


class InlineEditingNotificationTests(APITestCase):
    """Test notification sending for inline edits."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        self.goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Test Goal",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)
    
    def test_notification_sent_on_inline_edit(self):
        """Test that notification is sent to employee on inline edit."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check notification was created
        notifications = Notification.objects.filter(
            user=self.employee_user,
            goal=self.goal
        )
        
        assert notifications.exists()
        notification = notifications.latest('created_at')
        assert 'updated' in notification.title.lower()
        assert 'review' in notification.message.lower()
    
    def test_notification_contains_goal_info(self):
        """Test that notification contains goal information."""
        url = f'/api/goals/{self.goal.id}/edit_during_review/'
        data = {'title': 'Updated Title'}
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        notification = Notification.objects.filter(
            user=self.employee_user,
            goal=self.goal
        ).latest('created_at')
        
        assert self.goal.title in notification.message or 'Updated Title' in notification.message


class InlineEditingIntegrationTests(APITestCase):
    """Integration tests for inline editing workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Engineering")
        
        self.manager_user = User.objects.create_user(
            username='manager1',
            email='manager1@test.com',
            password='testpass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager_user,
            role='manager',
            department=self.department
        )
        
        self.employee_user = User.objects.create_user(
            username='employee1',
            email='employee1@test.com',
            password='testpass123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.employee_user,
            role='employee',
            department=self.department
        )
        
        self.cycle = Cycle.objects.create(
            name="Q1 FY2024",
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=90)).date()
        )
        
        self.thrust_area = ThrustArea.objects.create(name="Revenue Growth")
        self.uom_type = UoMType.objects.create(name='numeric')
        
        self.goal = Goal.objects.create(
            user=self.employee_user,
            cycle=self.cycle,
            title="Test Goal",
            description="Original description",
            thrust_area=self.thrust_area,
            uom_type=self.uom_type,
            target_value=100000,
            weightage=50,
            status='submitted'
        )
        
        self.client = APIClient()
    
    def test_complete_inline_editing_workflow(self):
        """Test complete workflow: edit -> approve."""
        self.client.force_authenticate(user=self.manager_user)
        
        # Step 1: Manager edits goal inline
        edit_url = f'/api/goals/{self.goal.id}/edit_during_review/'
        edit_data = {
            'title': 'Updated Sales Goal',
            'target_value': 150000,
            'weightage': 60
        }
        
        response = self.client.patch(edit_url, edit_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal was updated
        self.goal.refresh_from_db()
        assert self.goal.title == 'Updated Sales Goal'
        assert self.goal.target_value == 150000
        assert self.goal.weightage == 60
        
        # Step 2: Manager approves the edited goal
        approve_url = f'/api/goals/{self.goal.id}/approve/'
        response = self.client.post(approve_url, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal is now approved and locked
        self.goal.refresh_from_db()
        assert self.goal.status == 'approved'
        assert self.goal.approved_by == self.manager_user
    
    def test_inline_edit_then_reject_workflow(self):
        """Test workflow: edit -> reject."""
        self.client.force_authenticate(user=self.manager_user)
        
        # Step 1: Manager edits goal inline
        edit_url = f'/api/goals/{self.goal.id}/edit_during_review/'
        edit_data = {'title': 'Updated Title'}
        
        response = self.client.patch(edit_url, edit_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Step 2: Manager rejects the goal
        reject_url = f'/api/goals/{self.goal.id}/reject/'
        reject_data = {'comments': 'Needs more work'}
        response = self.client.post(reject_url, reject_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal is rejected
        self.goal.refresh_from_db()
        assert self.goal.status == 'rejected'
