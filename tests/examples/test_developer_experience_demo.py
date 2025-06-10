"""Demonstration of improved developer experience with automatic dataclass serialization.

This test shows the exact developer experience improvement achieved by the
automatic dataclass to dictionary conversion feature.
"""

import dataclasses
from datetime import datetime
from typing import Optional

import pytest

from pyopenapi_gen.core.utils import DataclassSerializer


@dataclasses.dataclass
class UserCreateRequest:
    """Example dataclass that a developer would define."""
    
    name: str
    email: str
    age: int
    bio: Optional[str] = None
    is_active: bool = True


@dataclasses.dataclass
class UserProfile:
    """Nested dataclass example."""
    
    website: Optional[str] = None
    linkedin: Optional[str] = None
    joined_at: datetime = dataclasses.field(default_factory=datetime.now)


@dataclasses.dataclass
class EnhancedUserRequest:
    """Complex nested dataclass example."""
    
    name: str
    email: str
    profile: UserProfile
    tags: list[str] = dataclasses.field(default_factory=list)


class TestDeveloperExperienceImprovement:
    """Demonstrate the developer experience improvement."""

    def test_before_vs_after_manual_conversion__shows_improvement__seamless_usage(self) -> None:
        """
        Scenario: Compare manual dictionary conversion vs automatic serialization
        Expected Outcome: Automatic serialization provides much better developer experience
        """
        
        # BEFORE: Developer had to manually convert dataclass to dict
        user_request = UserCreateRequest(
            name="John Doe",
            email="john@example.com", 
            age=30,
            bio="Software developer"
        )
        
        # Manual conversion (what developers had to do before)
        manual_dict = {
            "name": user_request.name,
            "email": user_request.email,
            "age": user_request.age,
            "bio": user_request.bio,
            "is_active": user_request.is_active,
        }
        
        # AFTER: Automatic serialization (what happens now)
        auto_dict = DataclassSerializer.serialize(user_request)
        
        # Results are equivalent
        expected = {
            "name": "John Doe",
            "email": "john@example.com", 
            "age": 30,
            "bio": "Software developer",
            "is_active": True,
        }
        
        assert manual_dict == expected
        assert auto_dict == expected
        
        # But automatic is much cleaner and less error-prone

    def test_complex_nested_structures__automatic_handling__no_manual_work(self) -> None:
        """
        Scenario: Complex nested dataclass with various types
        Expected Outcome: Automatic serialization handles all complexity seamlessly
        """
        
        # Complex nested structure that would be painful to convert manually
        profile = UserProfile(
            website="https://johndoe.dev",
            linkedin="https://linkedin.com/in/johndoe",
            joined_at=datetime(2023, 1, 15, 10, 30, 0)
        )
        
        user_request = EnhancedUserRequest(
            name="John Doe",
            email="john@example.com",
            profile=profile,
            tags=["python", "fastapi", "react"]
        )
        
        # Automatic serialization handles all the complexity
        result = DataclassSerializer.serialize(user_request)
        
        expected = {
            "name": "John Doe",
            "email": "john@example.com",
            "profile": {
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
                "joined_at": "2023-01-15T10:30:00"
            },
            "tags": ["python", "fastapi", "react"]
        }
        
        assert result == expected

    def test_generated_client_usage_example__seamless_api_calls__improved_dx(self) -> None:
        """
        Scenario: Show how generated client code now handles dataclass inputs seamlessly
        Expected Outcome: Developers can pass dataclass instances directly to API methods
        """
        
        # This demonstrates what generated client methods now do automatically
        
        # Developer creates a dataclass instance
        user_data = UserCreateRequest(
            name="Jane Smith",
            email="jane@example.com",
            age=28,
            bio="Product Manager"
        )
        
        # Simulate what the generated client method does under the hood
        def simulate_generated_client_method(body: UserCreateRequest) -> dict:
            """Simulates a generated client method with automatic serialization."""
            # This is what gets generated now:
            json_body = DataclassSerializer.serialize(body)
            
            # Then the actual HTTP request would use json_body
            # response = await self._transport.request("POST", url, json=json_body)
            
            return json_body
        
        # Developer can call the method directly with dataclass
        result = simulate_generated_client_method(user_data)
        
        expected = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 28,
            "bio": "Product Manager",
            "is_active": True
        }
        
        assert result == expected
        
        # Key benefit: No manual dict conversion needed!
        # Before: client.create_user(dataclasses.asdict(user_data))
        # After:  client.create_user(user_data)

    def test_optional_field_handling__clean_output__no_none_values(self) -> None:
        """
        Scenario: Test that optional None fields are properly excluded
        Expected Outcome: Clean JSON output without None values
        """
        
        # Create user without optional bio
        user_data = UserCreateRequest(
            name="Bob Wilson",
            email="bob@example.com",
            age=35
            # bio is None by default
        )
        
        result = DataclassSerializer.serialize(user_data)
        
        # Note: bio is not included because it's None
        expected = {
            "name": "Bob Wilson",
            "email": "bob@example.com",
            "age": 35,
            "is_active": True
        }
        
        assert result == expected
        assert "bio" not in result  # Clean output, no None values

    def test_developer_workflow_comparison__before_vs_after__clear_improvement(self) -> None:
        """
        Scenario: Complete workflow comparison showing the improvement
        Expected Outcome: Dramatic reduction in boilerplate and error potential
        """
        
        profile = UserProfile(website="https://example.com")
        user_request = EnhancedUserRequest(
            name="Developer",
            email="dev@example.com", 
            profile=profile,
            tags=["coding", "testing"]
        )
        
        # BEFORE: Manual conversion (error-prone, verbose)
        def manual_conversion_approach():
            # Developer had to write this manually for each dataclass
            profile_dict = {
                "website": user_request.profile.website,
                "linkedin": user_request.profile.linkedin,
                "joined_at": user_request.profile.joined_at.isoformat() if user_request.profile.joined_at else None
            }
            # Remove None values manually
            profile_dict = {k: v for k, v in profile_dict.items() if v is not None}
            
            request_dict = {
                "name": user_request.name,
                "email": user_request.email,
                "profile": profile_dict,
                "tags": user_request.tags
            }
            return request_dict
        
        # AFTER: Automatic conversion (clean, reliable)
        def automatic_conversion_approach():
            return DataclassSerializer.serialize(user_request)
        
        manual_result = manual_conversion_approach()
        auto_result = automatic_conversion_approach()
        
        # Results are equivalent
        assert manual_result == auto_result
        
        # But automatic approach is:
        # 1. Much shorter and cleaner
        # 2. Less error-prone (no manual field mapping)
        # 3. Handles nested structures automatically
        # 4. Properly handles None values and datetime serialization
        # 5. Works with any dataclass without code changes