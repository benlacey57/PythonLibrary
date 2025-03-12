# /home/{user}/scripts/python/library/core/data/validation.py

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Type, Optional, Callable, ClassVar
import re

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

@dataclass
class Validator:
    """Base validator class."""
    field_name: str
    message: str = "Validation failed"
    
    def validate(self, value: Any) -> bool:
        """Validate a value."""
        return True

@dataclass
class RequiredValidator(Validator):
    """Validator that ensures a value is not None."""
    message: str = "This field is required"
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        return True

@dataclass
class RegexValidator(Validator):
    """Validator that checks a string against a regex pattern."""
    pattern: str
    message: str = "Value does not match the required pattern"
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.match(self.pattern, value))

@dataclass
class RangeValidator(Validator):
    """Validator that checks a number is within a range."""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    message: str = "Value is out of range"
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, (int, float)):
            return False
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

class ValidatableMixin:
    """Mixin that adds validation capabilities to a dataclass."""
    
    _validators: ClassVar[Dict[str, List[Validator]]] = {}
    
    def validate(self) -> List[str]:
        """
        Validate the dataclass instance.
        
        Returns:
            List of error messages or empty list if valid.
        """
        errors = []
        
        # Get validators for this class
        validators = getattr(self.__class__, '_validators', {})
        
        # Run each validator
        for field_name, field_validators in validators.items():
            value = getattr(self, field_name, None)
            
            for validator in field_validators:
                if not validator.validate(value):
                    errors.append(f"{field_name}: {validator.message}")
        
        return errors
    
    @classmethod
    def add_validator(cls, field_name: str, validator: Validator) -> None:
        """
        Add a validator for a field.
        
        Args:
            field_name: Name of the field to validate.
            validator: Validator instance.
        """
        if not hasattr(cls, '_validators'):
            cls._validators = {}
            
        if field_name not in cls._validators:
            cls._validators[field_name] = []
            
        cls._validators[field_name].append(validator)