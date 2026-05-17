"""
Comprehensive tests for the validation engine.

Tests cover:
- Goal weightage validation (total = 100%, individual 10-100%)
- Goal count validation (max 8 per employee per cycle)
- Goal field validation (title, description, target value)
- Check-in validation (progress values, cycle periods)
- Shared goal validation (readonly fields)
- Cycle status validation
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    UserProfile, Department, ThrustArea, UoMType, Cycle, Goal, CheckIn
)
from .validators import (
    GoalWeightageValidator, GoalCountValidator, GoalFieldValidator,
    CheckInValidator, SharedGoalValidator, CycleStatusValidator,
    GoalValidator
)


# ============================================================================
# Goal Weightage Validator Tests
# ============================================================================

class GoalWeightageValidatorTestCase(TestCase):
    """Test cases for goal weightage validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.cycle = Cycle.objects.create(
            name='FY2024',
            start_date=datetime(2024, 4, 1).date(),
            end_date=datetime(2025, 3, 31).date()
        )
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue Growth')
        self.uom_type, _ = UoMType.objects.get_or_create(name='numeric')
    
    def test_validate_total_weightage_equals_100(self):
        """Test that total weightage of 100% is valid."""
        goals = [
            Goal(weightage=50),
            Goal(weightage=30),
            Goal(weightage=20)
        ]
        is_valid, total, error = GoalWeightageValidator.validate_total_weightage(goals)
        self.assertTrue(is_valid)
        self.assertEqual(total, 100.0)
        self.assertIsNone(error)
    
    def test_validate_total_weightage_not_100(self):
        """Test that total weightage not equal to 100% raises error."""
        goals = [
            Goal(weightage=50),
            Goal(weightage=30),
            Goal(weightage=15)  # Total = 95%
        ]
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_total_weightage(goals)
        self.assertIn("100%", str(context.exception))
    
    def test_validate_total_weightage_exceeds_100(self):
        """Test that total weightage exceeding 100% raises error."""
        goals = [
            Goal(weightage=60),
            Goal(weightage=50)  # Total = 110%
        ]
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_total_weightage(goals)
        self.assertIn("100%", str(context.exception))
    
    def test_validate_individual_weightage_valid_min(self):
        """Test that minimum valid weightage (10%) is accepted."""
        is_valid, error = GoalWeightageValidator.validate_individual_weightage(10)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_individual_weightage_valid_max(self):
        """Test that maximum valid weightage (100%) is accepted."""
        is_valid, error = GoalWeightageValidator.validate_individual_weightage(100)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_individual_weightage_valid_mid(self):
        """Test that mid-range weightage is accepted."""
        is_valid, error = GoalWeightageValidator.validate_individual_weightage(50)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_individual_weightage_below_min(self):
        """Test that weightage below 10% raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_individual_weightage(9)
        self.assertIn("10%", str(context.exception))
    
    def test_validate_individual_weightage_above_max(self):
        """Test that weightage above 100% raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_individual_weightage(101)
        self.assertIn("100%", str(context.exception))
    
    def test_validate_individual_weightage_invalid_type(self):
        """Test that non-numeric weightage raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_individual_weightage("invalid")
        self.assertIn("valid number", str(context.exception))
    
    def test_validate_weightage_for_update_valid(self):
        """Test weightage validation for goal update."""
        # Create existing goals with 70% total
        Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Goal 1',
            thrust_area=self.uom_type, uom_type=self.uom_type,
            target_value=100, weightage=40
        )
        Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Goal 2',
            thrust_area=self.uom_type, uom_type=self.uom_type,
            target_value=100, weightage=30
        )
        
        # Adding 30% should be valid (total = 100%)
        is_valid, new_total, error = GoalWeightageValidator.validate_weightage_for_update(
            self.user, self.cycle, 30
        )
        self.assertTrue(is_valid)
        self.assertEqual(new_total, 100.0)
    
    def test_validate_weightage_for_update_exceeds_100(self):
        """Test that adding weightage exceeding 100% raises error."""
        # Create existing goals with 70% total
        Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Goal 1',
            thrust_area=self.uom_type, uom_type=self.uom_type,
            target_value=100, weightage=70
        )
        
        # Adding 40% should exceed 100%
        with self.assertRaises(ValidationError) as context:
            GoalWeightageValidator.validate_weightage_for_update(
                self.user, self.cycle, 40
            )
        self.assertIn("exceed", str(context.exception))


# ============================================================================
# Goal Count Validator Tests
# ============================================================================

class GoalCountValidatorTestCase(TestCase):
    """Test cases for goal count validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.cycle = Cycle.objects.create(
            name='FY2024',
            start_date=datetime(2024, 4, 1).date(),
            end_date=datetime(2025, 3, 31).date()
        )
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue Growth')
        self.uom_type, _ = UoMType.objects.get_or_create(name='numeric')
    
    def test_validate_goal_count_below_max(self):
        """Test that goal count below max is valid."""
        # Create 5 goals
        for i in range(5):
            Goal.objects.create(
                user=self.user, cycle=self.cycle, title=f'Goal {i}',
                thrust_area=self.thrust_area, uom_type=self.uom_type,
                target_value=100, weightage=20
            )
        
        is_valid, count, max_count, error = GoalCountValidator.validate_goal_count(
            self.user, self.cycle
        )
        self.assertTrue(is_valid)
        self.assertEqual(count, 5)
        self.assertEqual(max_count, 8)
    
    def test_validate_goal_count_at_max(self):
        """Test that goal count at max raises error."""
        # Create 8 goals (at max)
        for i in range(8):
            Goal.objects.create(
                user=self.user, cycle=self.cycle, title=f'Goal {i}',
                thrust_area=self.thrust_area, uom_type=self.uom_type,
                target_value=100, weightage=12.5
            )
        
        with self.assertRaises(ValidationError) as context:
            GoalCountValidator.validate_goal_count(self.user, self.cycle)
        self.assertIn("Maximum 8", str(context.exception))
    
    def test_get_goal_count(self):
        """Test getting current goal count."""
        # Create 3 goals
        for i in range(3):
            Goal.objects.create(
                user=self.user, cycle=self.cycle, title=f'Goal {i}',
                thrust_area=self.thrust_area, uom_type=self.uom_type,
                target_value=100, weightage=33.33
            )
        
        count = GoalCountValidator.get_goal_count(self.user, self.cycle)
        self.assertEqual(count, 3)
    
    def test_get_remaining_capacity(self):
        """Test getting remaining goal capacity."""
        # Create 3 goals
        for i in range(3):
            Goal.objects.create(
                user=self.user, cycle=self.cycle, title=f'Goal {i}',
                thrust_area=self.thrust_area, uom_type=self.uom_type,
                target_value=100, weightage=33.33
            )
        
        remaining = GoalCountValidator.get_remaining_capacity(self.user, self.cycle)
        self.assertEqual(remaining, 5)  # 8 - 3 = 5


# ============================================================================
# Goal Field Validator Tests
# ============================================================================

class GoalFieldValidatorTestCase(TestCase):
    """Test cases for goal field validation."""
    
    def test_validate_title_valid(self):
        """Test that valid title is accepted."""
        is_valid, error = GoalFieldValidator.validate_title("Increase Revenue by 20%")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_title_empty(self):
        """Test that empty title raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_title("")
        self.assertIn("required", str(context.exception))
    
    def test_validate_title_whitespace_only(self):
        """Test that whitespace-only title raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_title("   ")
        self.assertIn("empty", str(context.exception))
    
    def test_validate_title_exceeds_max_length(self):
        """Test that title exceeding 255 chars raises error."""
        long_title = "A" * 256
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_title(long_title)
        self.assertIn("255", str(context.exception))
    
    def test_validate_title_at_max_length(self):
        """Test that title at exactly 255 chars is valid."""
        title = "A" * 255
        is_valid, error = GoalFieldValidator.validate_title(title)
        self.assertTrue(is_valid)
    
    def test_validate_title_not_string(self):
        """Test that non-string title raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_title(123)
        self.assertIn("string", str(context.exception))
    
    def test_validate_description_valid(self):
        """Test that valid description is accepted."""
        is_valid, error = GoalFieldValidator.validate_description("This is a goal description")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_description_empty(self):
        """Test that empty description is valid."""
        is_valid, error = GoalFieldValidator.validate_description("")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_description_exceeds_max_length(self):
        """Test that description exceeding 2000 chars raises error."""
        long_desc = "A" * 2001
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_description(long_desc)
        self.assertIn("2000", str(context.exception))
    
    def test_validate_description_at_max_length(self):
        """Test that description at exactly 2000 chars is valid."""
        desc = "A" * 2000
        is_valid, error = GoalFieldValidator.validate_description(desc)
        self.assertTrue(is_valid)
    
    def test_validate_target_value_valid_positive(self):
        """Test that positive target value is valid."""
        is_valid, error = GoalFieldValidator.validate_target_value(100)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_target_value_valid_zero(self):
        """Test that zero target value is valid."""
        is_valid, error = GoalFieldValidator.validate_target_value(0)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_target_value_negative(self):
        """Test that negative target value raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_target_value(-10)
        self.assertIn("non-negative", str(context.exception))
    
    def test_validate_target_value_invalid_type(self):
        """Test that non-numeric target value raises error."""
        with self.assertRaises(ValidationError) as context:
            GoalFieldValidator.validate_target_value("invalid")
        self.assertIn("valid number", str(context.exception))


# ============================================================================
# Check-in Validator Tests
# ============================================================================

class CheckInValidatorTestCase(TestCase):
    """Test cases for check-in validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.cycle = Cycle.objects.create(
            name='FY2024',
            start_date=datetime(2024, 4, 1).date(),
            end_date=datetime(2025, 3, 31).date()
        )
        self.cycle.set_checkin_dates()
        self.cycle.save()
        
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue Growth')
        self.uom_numeric, _ = UoMType.objects.get_or_create(name='numeric')
        self.uom_percentage, _ = UoMType.objects.get_or_create(name='percentage')
        self.uom_zero_based, _ = UoMType.objects.get_or_create(name='zero_based')
        
        self.goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Test Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_numeric,
            target_value=100, weightage=100, status='approved'
        )
    
    def test_validate_progress_value_numeric_valid(self):
        """Test that valid numeric progress value is accepted."""
        is_valid, error = CheckInValidator.validate_progress_value(self.goal, 50)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_progress_value_numeric_exceeds_target(self):
        """Test that numeric progress exceeding target is accepted (capped at 100%)."""
        is_valid, error = CheckInValidator.validate_progress_value(self.goal, 150)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_progress_value_numeric_negative(self):
        """Test that negative numeric progress raises error."""
        with self.assertRaises(ValidationError) as context:
            CheckInValidator.validate_progress_value(self.goal, -10)
        self.assertIn("negative", str(context.exception))
    
    def test_validate_progress_value_percentage_valid(self):
        """Test that valid percentage progress is accepted."""
        goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Percentage Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_percentage,
            target_value=100, weightage=100, status='approved'
        )
        is_valid, error = CheckInValidator.validate_progress_value(goal, 75)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_progress_value_percentage_exceeds_100(self):
        """Test that percentage progress exceeding 100% raises error."""
        goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Percentage Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_percentage,
            target_value=100, weightage=100, status='approved'
        )
        with self.assertRaises(ValidationError) as context:
            CheckInValidator.validate_progress_value(goal, 101)
        self.assertIn("0 and 100", str(context.exception))
    
    def test_validate_progress_value_zero_based_zero(self):
        """Test that zero value for zero-based goal is valid."""
        goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Zero-based Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_zero_based,
            target_value=1, weightage=100, status='approved'
        )
        is_valid, error = CheckInValidator.validate_progress_value(goal, 0)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_progress_value_zero_based_nonzero(self):
        """Test that non-zero value for zero-based goal is valid."""
        goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Zero-based Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_zero_based,
            target_value=1, weightage=100, status='approved'
        )
        is_valid, error = CheckInValidator.validate_progress_value(goal, 1)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_goal_approved_valid(self):
        """Test that approved goal passes validation."""
        is_valid, error = CheckInValidator.validate_goal_approved(self.goal)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_goal_approved_draft(self):
        """Test that draft goal raises error."""
        goal = Goal.objects.create(
            user=self.user, cycle=self.cycle, title='Draft Goal',
            thrust_area=self.thrust_area, uom_type=self.uom_numeric,
            target_value=100, weightage=100, status='draft'
        )
        with self.assertRaises(ValidationError) as context:
            CheckInValidator.validate_goal_approved(goal)
        self.assertIn("approved", str(context.exception))
    
    def test_validate_checkin_period_active(self):
        """Test that check-in during active period is valid."""
        # Q1 check-in date is July 15
        checkin_date = self.cycle.checkin_date_q1
        is_valid, period, error = CheckInValidator.validate_checkin_period(
            self.cycle, checkin_date
        )
        self.assertTrue(is_valid)
        self.assertEqual(period, 'Q1')
    
    def test_validate_checkin_period_inactive(self):
        """Test that check-in outside active period raises error."""
        # Use a date far from any check-in period
        inactive_date = datetime(2024, 5, 1).date()
        with self.assertRaises(ValidationError) as context:
            CheckInValidator.validate_checkin_period(self.cycle, inactive_date)
        self.assertIn("not active", str(context.exception))


# ============================================================================
# Cycle Status Validator Tests
# ============================================================================

class CycleStatusValidatorTestCase(TestCase):
    """Test cases for cycle status validation."""
    
    def setUp(self):
        """Set up test data."""
        self.active_cycle = Cycle.objects.create(
            name='Active Cycle',
            start_date=datetime(2024, 4, 1).date(),
            end_date=datetime(2025, 3, 31).date(),
            status='active'
        )
        self.planning_cycle = Cycle.objects.create(
            name='Planning Cycle',
            start_date=datetime(2025, 4, 1).date(),
            end_date=datetime(2026, 3, 31).date(),
            status='planning'
        )
        self.closed_cycle = Cycle.objects.create(
            name='Closed Cycle',
            start_date=datetime(2023, 4, 1).date(),
            end_date=datetime(2024, 3, 31).date(),
            status='closed'
        )
    
    def test_validate_cycle_active_for_goals_valid(self):
        """Test that active cycle allows goal creation."""
        is_valid, error = CycleStatusValidator.validate_cycle_active_for_goals(
            self.active_cycle
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_cycle_active_for_goals_planning(self):
        """Test that planning cycle prevents goal creation."""
        with self.assertRaises(ValidationError) as context:
            CycleStatusValidator.validate_cycle_active_for_goals(self.planning_cycle)
        self.assertIn("active", str(context.exception))
    
    def test_validate_cycle_active_for_goals_closed(self):
        """Test that closed cycle prevents goal creation."""
        with self.assertRaises(ValidationError) as context:
            CycleStatusValidator.validate_cycle_active_for_goals(self.closed_cycle)
        self.assertIn("active", str(context.exception))
    
    def test_validate_cycle_active_for_checkins_valid(self):
        """Test that active cycle allows check-in submission."""
        is_valid, error = CycleStatusValidator.validate_cycle_active_for_checkins(
            self.active_cycle
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_cycle_active_for_checkins_closed(self):
        """Test that closed cycle prevents check-in submission."""
        with self.assertRaises(ValidationError) as context:
            CycleStatusValidator.validate_cycle_active_for_checkins(self.closed_cycle)
        self.assertIn("active", str(context.exception))


# ============================================================================
# Composite Validator Tests
# ============================================================================

class GoalValidatorTestCase(TestCase):
    """Test cases for composite goal validator."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.active_cycle = Cycle.objects.create(
            name='Active Cycle',
            start_date=datetime(2024, 4, 1).date(),
            end_date=datetime(2025, 3, 31).date(),
            status='active'
        )
        self.thrust_area, _ = ThrustArea.objects.get_or_create(name='Revenue Growth')
        self.uom_type, _ = UoMType.objects.get_or_create(name='numeric')
    
    def test_validate_goal_creation_valid(self):
        """Test that valid goal data passes all validations."""
        goal_data = {
            'title': 'Increase Revenue',
            'description': 'Increase revenue by 20%',
            'target_value': 100,
            'weightage': 50
        }
        is_valid, errors = GoalValidator.validate_goal_creation(
            self.user, self.active_cycle, goal_data
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_goal_creation_invalid_title(self):
        """Test that invalid title is caught."""
        goal_data = {
            'title': '',
            'description': 'Valid description',
            'target_value': 100,
            'weightage': 50
        }
        with self.assertRaises(ValidationError):
            GoalValidator.validate_goal_creation(
                self.user, self.active_cycle, goal_data
            )
    
    def test_validate_goal_creation_invalid_weightage(self):
        """Test that invalid weightage is caught."""
        goal_data = {
            'title': 'Valid Title',
            'description': 'Valid description',
            'target_value': 100,
            'weightage': 5  # Below minimum
        }
        with self.assertRaises(ValidationError):
            GoalValidator.validate_goal_creation(
                self.user, self.active_cycle, goal_data
            )
