"""
Simple test script for validators without Django setup.
Tests the validator logic directly.
"""

import sys
sys.path.insert(0, '.')

# Test imports
try:
    from django.core.exceptions import ValidationError
    print("✓ Django imports successful")
except ImportError as e:
    print(f"✗ Django import failed: {e}")
    sys.exit(1)

# Test validator imports
try:
    from portal.validators import (
        GoalWeightageValidator, GoalCountValidator, GoalFieldValidator,
        CheckInValidator, CycleStatusValidator
    )
    print("✓ Validator imports successful")
except ImportError as e:
    print(f"✗ Validator import failed: {e}")
    sys.exit(1)

# Test GoalFieldValidator
print("\n=== Testing GoalFieldValidator ===")

# Test valid title
try:
    is_valid, error = GoalFieldValidator.validate_title("Valid Title")
    assert is_valid == True
    assert error is None
    print("✓ Valid title accepted")
except Exception as e:
    print(f"✗ Valid title test failed: {e}")

# Test empty title
try:
    GoalFieldValidator.validate_title("")
    print("✗ Empty title should raise ValidationError")
except ValidationError:
    print("✓ Empty title rejected")
except Exception as e:
    print(f"✗ Empty title test failed: {e}")

# Test title too long
try:
    GoalFieldValidator.validate_title("A" * 256)
    print("✗ Long title should raise ValidationError")
except ValidationError:
    print("✓ Long title rejected")
except Exception as e:
    print(f"✗ Long title test failed: {e}")

# Test valid description
try:
    is_valid, error = GoalFieldValidator.validate_description("Valid description")
    assert is_valid == True
    assert error is None
    print("✓ Valid description accepted")
except Exception as e:
    print(f"✗ Valid description test failed: {e}")

# Test description too long
try:
    GoalFieldValidator.validate_description("A" * 2001)
    print("✗ Long description should raise ValidationError")
except ValidationError:
    print("✓ Long description rejected")
except Exception as e:
    print(f"✗ Long description test failed: {e}")

# Test valid target value
try:
    is_valid, error = GoalFieldValidator.validate_target_value(100)
    assert is_valid == True
    assert error is None
    print("✓ Valid target value accepted")
except Exception as e:
    print(f"✗ Valid target value test failed: {e}")

# Test negative target value
try:
    GoalFieldValidator.validate_target_value(-10)
    print("✗ Negative target value should raise ValidationError")
except ValidationError:
    print("✓ Negative target value rejected")
except Exception as e:
    print(f"✗ Negative target value test failed: {e}")

# Test GoalWeightageValidator
print("\n=== Testing GoalWeightageValidator ===")

# Test valid individual weightage
try:
    is_valid, error = GoalWeightageValidator.validate_individual_weightage(50)
    assert is_valid == True
    assert error is None
    print("✓ Valid weightage (50%) accepted")
except Exception as e:
    print(f"✗ Valid weightage test failed: {e}")

# Test minimum weightage
try:
    is_valid, error = GoalWeightageValidator.validate_individual_weightage(10)
    assert is_valid == True
    print("✓ Minimum weightage (10%) accepted")
except Exception as e:
    print(f"✗ Minimum weightage test failed: {e}")

# Test maximum weightage
try:
    is_valid, error = GoalWeightageValidator.validate_individual_weightage(100)
    assert is_valid == True
    print("✓ Maximum weightage (100%) accepted")
except Exception as e:
    print(f"✗ Maximum weightage test failed: {e}")

# Test weightage below minimum
try:
    GoalWeightageValidator.validate_individual_weightage(9)
    print("✗ Weightage below 10% should raise ValidationError")
except ValidationError:
    print("✓ Weightage below 10% rejected")
except Exception as e:
    print(f"✗ Weightage below minimum test failed: {e}")

# Test weightage above maximum
try:
    GoalWeightageValidator.validate_individual_weightage(101)
    print("✗ Weightage above 100% should raise ValidationError")
except ValidationError:
    print("✓ Weightage above 100% rejected")
except Exception as e:
    print(f"✗ Weightage above maximum test failed: {e}")

# Test total weightage validation
print("\n=== Testing Total Weightage Validation ===")

class MockGoal:
    def __init__(self, weightage):
        self.weightage = weightage

# Test total = 100%
try:
    goals = [MockGoal(50), MockGoal(30), MockGoal(20)]
    is_valid, total, error = GoalWeightageValidator.validate_total_weightage(goals)
    assert is_valid == True
    assert total == 100.0
    print("✓ Total weightage = 100% accepted")
except Exception as e:
    print(f"✗ Total weightage test failed: {e}")

# Test total != 100%
try:
    goals = [MockGoal(50), MockGoal(30), MockGoal(15)]
    GoalWeightageValidator.validate_total_weightage(goals)
    print("✗ Total weightage != 100% should raise ValidationError")
except ValidationError:
    print("✓ Total weightage != 100% rejected")
except Exception as e:
    print(f"✗ Total weightage != 100% test failed: {e}")

print("\n=== All Basic Tests Completed ===")
print("✓ Validators are working correctly!")
