"""
Validation engine for goal constraints and business rules.

This module provides comprehensive validation for:
- Goal weightage constraints (total = 100%, individual 10-100%)
- Goal count constraints (max 8 per employee per cycle)
- Goal field constraints (title, description, target value)
- Check-in constraints (progress values, cycle periods)
"""

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from decimal import Decimal
import re


# ============================================================================
# Goal Weightage Validators
# ============================================================================

class GoalWeightageValidator:
    """Validator for goal weightage constraints."""
    
    @staticmethod
    def validate_total_weightage(goals, tolerance=0.01):
        """
        Validate that total weightage equals 100%.
        
        Args:
            goals: List of Goal objects or queryset
            tolerance: Floating point tolerance (default 0.01 for rounding)
        
        Returns:
            Tuple: (is_valid, total_weightage, error_message)
        
        Raises:
            ValidationError: If total weightage is not 100%
        """
        if not goals:
            raise ValidationError("No goals provided for weightage validation.")
        
        total = sum(float(goal.weightage) for goal in goals)
        
        # Allow small tolerance for floating point arithmetic
        if abs(total - 100.0) > tolerance:
            error_msg = f"Total weightage must be exactly 100%. Current total: {total:.2f}%"
            raise ValidationError(error_msg)
        
        return True, total, None
    
    @staticmethod
    def validate_individual_weightage(weightage):
        """
        Validate that individual goal weightage is between 10% and 100%.
        
        Args:
            weightage: Weightage value (float or Decimal)
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If weightage is outside valid range
        """
        try:
            weightage_float = float(weightage)
        except (TypeError, ValueError):
            raise ValidationError("Weightage must be a valid number.")
        
        if weightage_float < 10 or weightage_float > 100:
            error_msg = "Weightage must be between 10% and 100%."
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_weightage_for_update(user, cycle, new_weightage, exclude_goal_id=None):
        """
        Validate that adding/updating a goal with new weightage keeps total at 100%.
        
        Args:
            user: User object
            cycle: Cycle object
            new_weightage: New weightage value
            exclude_goal_id: Goal ID to exclude from calculation (for updates)
        
        Returns:
            Tuple: (is_valid, new_total, error_message)
        
        Raises:
            ValidationError: If total would exceed 100%
        """
        from .models import Goal
        
        # Validate individual weightage first
        GoalWeightageValidator.validate_individual_weightage(new_weightage)
        
        # Get existing goals
        query = Goal.objects.filter(user=user, cycle=cycle)
        if exclude_goal_id:
            query = query.exclude(id=exclude_goal_id)
        
        existing_total = sum(float(goal.weightage) for goal in query)
        new_total = existing_total + float(new_weightage)
        
        if new_total > 100:
            error_msg = f"Adding this goal would exceed 100% total. Current: {existing_total:.2f}%, New: {new_weightage}%"
            raise ValidationError(error_msg)
        
        return True, new_total, None


# ============================================================================
# Goal Count Validators
# ============================================================================

class GoalCountValidator:
    """Validator for goal count constraints."""
    
    MAX_GOALS_PER_CYCLE = 8
    
    @staticmethod
    def validate_goal_count(user, cycle, exclude_goal_id=None):
        """
        Validate that user doesn't exceed max 8 goals per cycle.
        
        Args:
            user: User object
            cycle: Cycle object
            exclude_goal_id: Goal ID to exclude from count (for updates)
        
        Returns:
            Tuple: (is_valid, current_count, max_count, error_message)
        
        Raises:
            ValidationError: If user already has max goals
        """
        from .models import Goal
        
        query = Goal.objects.filter(user=user, cycle=cycle)
        if exclude_goal_id:
            query = query.exclude(id=exclude_goal_id)
        
        current_count = query.count()
        max_count = GoalCountValidator.MAX_GOALS_PER_CYCLE
        
        if current_count >= max_count:
            error_msg = f"Maximum {max_count} goals allowed per cycle. You already have {current_count} goals."
            raise ValidationError(error_msg)
        
        return True, current_count, max_count, None
    
    @staticmethod
    def get_goal_count(user, cycle):
        """
        Get current goal count for user in cycle.
        
        Args:
            user: User object
            cycle: Cycle object
        
        Returns:
            Integer: Current goal count
        """
        from .models import Goal
        return Goal.objects.filter(user=user, cycle=cycle).count()
    
    @staticmethod
    def get_remaining_capacity(user, cycle):
        """
        Get remaining goal capacity for user in cycle.
        
        Args:
            user: User object
            cycle: Cycle object
        
        Returns:
            Integer: Remaining capacity (0-8)
        """
        current = GoalCountValidator.get_goal_count(user, cycle)
        return max(0, GoalCountValidator.MAX_GOALS_PER_CYCLE - current)


# ============================================================================
# Goal Field Validators
# ============================================================================

class GoalFieldValidator:
    """Validator for goal field constraints."""
    
    TITLE_MAX_LENGTH = 255
    DESCRIPTION_MAX_LENGTH = 2000
    
    @staticmethod
    def validate_title(title):
        """
        Validate goal title.
        
        Constraints:
        - Non-empty
        - Max 255 characters
        
        Args:
            title: Goal title string
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If title is invalid
        """
        if not title or not isinstance(title, str):
            raise ValidationError("Goal title is required and must be a string.")
        
        title_stripped = title.strip()
        if not title_stripped:
            raise ValidationError("Goal title cannot be empty or contain only whitespace.")
        
        if len(title_stripped) > GoalFieldValidator.TITLE_MAX_LENGTH:
            error_msg = f"Goal title cannot exceed {GoalFieldValidator.TITLE_MAX_LENGTH} characters. Current length: {len(title_stripped)}"
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_description(description):
        """
        Validate goal description.
        
        Constraints:
        - Max 2000 characters
        - Can be empty
        
        Args:
            description: Goal description string
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If description is invalid
        """
        if description is None:
            description = ""
        
        if not isinstance(description, str):
            raise ValidationError("Goal description must be a string.")
        
        if len(description) > GoalFieldValidator.DESCRIPTION_MAX_LENGTH:
            error_msg = f"Goal description cannot exceed {GoalFieldValidator.DESCRIPTION_MAX_LENGTH} characters. Current length: {len(description)}"
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_target_value(target_value):
        """
        Validate goal target value.
        
        Constraints:
        - Non-negative number (zero or positive)
        - Must be numeric
        
        Args:
            target_value: Target value (float, int, or Decimal)
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If target value is invalid
        """
        try:
            target_float = float(target_value)
        except (TypeError, ValueError):
            raise ValidationError("Target value must be a valid number.")
        
        if target_float < 0:
            raise ValidationError("Target value must be non-negative (zero or positive).")
        
        return True, None


# ============================================================================
# Check-in Validators
# ============================================================================

# ============================================================================
# Check-in Validators (see composite CheckInValidator class below)
# ============================================================================


# ============================================================================
# Shared Goal Validators
# ============================================================================

class SharedGoalValidator:
    """Validator for shared goal constraints."""
    
    @staticmethod
    def validate_readonly_fields(goal, data):
        """
        Validate that readonly fields of shared goals are not modified.
        
        Args:
            goal: Goal object (must be a shared goal)
            data: Dictionary of fields being updated
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If readonly fields are being modified
        """
        if not goal.is_shared:
            return True, None
        
        readonly_errors = []
        
        if goal.is_readonly_title and 'title' in data:
            if data['title'] != goal.title:
                readonly_errors.append("Goal title is read-only for shared goals.")
        
        if goal.is_readonly_target and 'target_value' in data:
            if float(data['target_value']) != float(goal.target_value):
                readonly_errors.append("Goal target value is read-only for shared goals.")
        
        if readonly_errors:
            raise ValidationError(" ".join(readonly_errors))
        
        return True, None


# ============================================================================
# Cycle Status Validators
# ============================================================================

class CycleStatusValidator:
    """Validator for cycle status constraints."""
    
    @staticmethod
    def validate_cycle_active_for_goals(cycle):
        """
        Validate that cycle is active for goal creation.
        
        Args:
            cycle: Cycle object
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If cycle is not active
        """
        if cycle.status != 'active':
            error_msg = f"Goal creation is only allowed during active cycles. Current cycle status: {cycle.get_status_display()}"
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_cycle_active_for_checkins(cycle):
        """
        Validate that cycle is active for check-in submissions.
        
        Args:
            cycle: Cycle object
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If cycle is not active
        """
        if cycle.status != 'active':
            error_msg = f"Check-in submissions are only allowed during active cycles. Current cycle status: {cycle.get_status_display()}"
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_goal_not_edited_after_cycle_closure(goal, cycle):
        """
        Validate that goal cannot be edited after cycle closure.
        
        Args:
            goal: Goal object
            cycle: Cycle object
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If cycle is closed
        """
        if cycle.status == 'closed':
            error_msg = "Goals cannot be edited after cycle closure."
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_checkin_not_edited_after_cycle_closure(checkin, cycle):
        """
        Validate that check-in cannot be edited after cycle closure.
        
        Args:
            checkin: CheckIn object
            cycle: Cycle object
        
        Returns:
            Tuple: (is_valid, error_message)
        
        Raises:
            ValidationError: If cycle is closed
        """
        if cycle.status == 'closed':
            error_msg = "Check-ins cannot be edited after cycle closure."
            raise ValidationError(error_msg)
        
        return True, None
    
    @staticmethod
    def validate_only_one_active_cycle():
        """
        Validate that only one cycle is active at a time.
        
        Returns:
            Tuple: (is_valid, active_cycle_count, error_message)
        
        Raises:
            ValidationError: If more than one active cycle exists
        """
        from .models import Cycle
        
        active_cycles = Cycle.objects.filter(status='active').count()
        
        if active_cycles > 1:
            error_msg = f"Only one active cycle is allowed at a time. Currently {active_cycles} cycles are active."
            raise ValidationError(error_msg)
        
        return True, active_cycles, None


# ============================================================================
# Composite Validators
# ============================================================================

class GoalValidator:
    """Composite validator for complete goal validation."""
    
    @staticmethod
    def validate_goal_creation(user, cycle, goal_data):
        """
        Validate all constraints for goal creation.
        
        Args:
            user: User object
            cycle: Cycle object
            goal_data: Dictionary with goal fields
        
        Returns:
            Tuple: (is_valid, errors)
        
        Raises:
            ValidationError: If any validation fails
        """
        errors = []
        
        try:
            # Validate cycle status
            CycleStatusValidator.validate_cycle_active_for_goals(cycle)
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate goal count
            GoalCountValidator.validate_goal_count(user, cycle)
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate title
            GoalFieldValidator.validate_title(goal_data.get('title', ''))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate description
            GoalFieldValidator.validate_description(goal_data.get('description', ''))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate target value
            GoalFieldValidator.validate_target_value(goal_data.get('target_value', 0))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate individual weightage
            GoalWeightageValidator.validate_individual_weightage(goal_data.get('weightage', 0))
        except ValidationError as e:
            errors.append(str(e))
        
        if errors:
            raise ValidationError(errors)
        
        return True, []
    
    @staticmethod
    def validate_goal_update(goal, goal_data):
        """
        Validate all constraints for goal update.
        
        Args:
            goal: Goal object being updated
            goal_data: Dictionary with updated fields
        
        Returns:
            Tuple: (is_valid, errors)
        
        Raises:
            ValidationError: If any validation fails
        """
        errors = []
        
        # Validate title if provided
        if 'title' in goal_data:
            try:
                GoalFieldValidator.validate_title(goal_data['title'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate description if provided
        if 'description' in goal_data:
            try:
                GoalFieldValidator.validate_description(goal_data['description'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate target value if provided
        if 'target_value' in goal_data:
            try:
                GoalFieldValidator.validate_target_value(goal_data['target_value'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate weightage if provided
        if 'weightage' in goal_data:
            try:
                GoalWeightageValidator.validate_individual_weightage(goal_data['weightage'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate shared goal readonly fields
        if goal.is_shared:
            try:
                SharedGoalValidator.validate_readonly_fields(goal, goal_data)
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError(errors)
        
        return True, []


class CheckInValidator:
    """Composite validator for complete check-in validation."""
    
    @staticmethod
    def validate_progress_value(goal, progress_value):
        """Validate check-in progress value based on UoM type."""
        if goal.uom_type is None:
            raise ValidationError("Goal must have a UoM type defined.")
        
        try:
            progress_float = float(progress_value)
        except (TypeError, ValueError):
            raise ValidationError("Progress value must be a valid number.")
        
        uom_name = goal.uom_type.name
        
        if uom_name == 'numeric':
            if progress_float < 0:
                raise ValidationError("Progress value cannot be negative.")
            return True, None
        elif uom_name == 'percentage':
            if progress_float < 0 or progress_float > 100:
                raise ValidationError("Percentage progress must be between 0 and 100.")
            return True, None
        elif uom_name == 'timeline':
            return True, None
        elif uom_name == 'zero_based':
            if progress_float < 0:
                raise ValidationError("Progress value cannot be negative.")
            return True, None
        else:
            raise ValidationError(f"Unknown UoM type: {uom_name}")
    
    @staticmethod
    def validate_goal_approved(goal):
        """Validate that goal is approved before check-in submission."""
        if goal.status != 'approved':
            error_msg = f"Goal must be approved before submitting check-in. Current status: {goal.get_status_display()}"
            raise ValidationError(error_msg)
        return True, None
    
    @staticmethod
    def validate_checkin_period(cycle, current_date=None):
        """Validate that current date is within an active check-in period."""
        from django.utils import timezone
        from datetime import timedelta
        
        if current_date is None:
            current_date = timezone.now().date()
        
        periods = [
            ('Q1', cycle.checkin_date_q1),
            ('Q2', cycle.checkin_date_q2),
            ('Q3', cycle.checkin_date_q3),
            ('Q4', cycle.checkin_date_q4),
        ]
        
        for period_name, checkin_date in periods:
            if checkin_date:
                period_start = checkin_date - timedelta(days=7)
                period_end = checkin_date + timedelta(days=7)
                if period_start <= current_date <= period_end:
                    return True, period_name, None
        
        next_checkin = None
        for period_name, checkin_date in periods:
            if checkin_date and checkin_date > current_date:
                if next_checkin is None or checkin_date < next_checkin:
                    next_checkin = checkin_date
        
        if next_checkin:
            error_msg = f"Check-in cycle is not active. Next check-in period: {next_checkin.strftime('%B %d, %Y')}"
        else:
            error_msg = "Check-in cycle is not active. No upcoming check-in periods found."
        
        raise ValidationError(error_msg)
    
    @staticmethod
    def validate_checkin_submission(goal, cycle, progress_value, current_date=None):
        """
        Validate all constraints for check-in submission.
        
        Args:
            goal: Goal object
            cycle: Cycle object
            progress_value: Progress value
            current_date: Current date (defaults to today)
        
        Returns:
            Tuple: (is_valid, errors)
        
        Raises:
            ValidationError: If any validation fails
        """
        errors = []
        
        try:
            CycleStatusValidator.validate_cycle_active_for_checkins(cycle)
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            CheckInValidator.validate_goal_approved(goal)
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            CheckInValidator.validate_checkin_period(cycle, current_date)
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            CheckInValidator.validate_progress_value(goal, progress_value)
        except ValidationError as e:
            errors.append(str(e))
        
        if errors:
            raise ValidationError(errors)
        
        return True, []
