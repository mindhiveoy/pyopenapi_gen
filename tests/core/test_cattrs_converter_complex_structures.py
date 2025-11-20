"""
Comprehensive tests for cattrs converter with complex and edge-case JSON structures.

Tests various real-world API response patterns including:
- Arrays at root level
- Deeply nested objects (3+ levels)
- Arrays of arrays
- Mixed complex structures
- Edge cases and special values
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from pyopenapi_gen.core.cattrs_converter import structure_from_dict, unstructure_to_dict

# ===== Test 1: Array at Root Level =====


@dataclass
class UserSimple:
    """Simple user model for array responses."""

    user_id: int  # Maps from 'userId'
    user_name: str  # Maps from 'userName'
    is_active: bool  # Maps from 'isActive'

    class Meta:
        key_transform_with_load = {
            "userId": "user_id",
            "userName": "user_name",
            "isActive": "is_active",
        }
        key_transform_with_dump = {
            "user_id": "userId",
            "user_name": "userName",
            "is_active": "isActive",
        }


def test_structure_from_dict__array_at_root__structures_correctly():
    """
    Test structuring when JSON root is an array, not an object.

    Scenario:
        Some API endpoints return arrays directly without wrapper objects.
        Example: GET /users returns [{"userId": 1, ...}, {"userId": 2, ...}]

    Expected Outcome:
        List of dataclass instances with proper field name transformation.
    """
    # Arrange: JSON array at root
    json_response = [
        {"userId": 1, "userName": "Alice", "isActive": True},
        {"userId": 2, "userName": "Bob", "isActive": False},
        {"userId": 3, "userName": "Charlie", "isActive": True},
    ]

    # Act: Structure as List[UserSimple]
    result = [structure_from_dict(item, UserSimple) for item in json_response]

    # Assert
    assert len(result) == 3
    assert all(isinstance(user, UserSimple) for user in result)
    assert result[0].user_id == 1
    assert result[0].user_name == "Alice"
    assert result[0].is_active is True
    assert result[1].user_id == 2
    assert result[2].user_id == 3


# ===== Test 2: Deeply Nested Objects (3+ levels) =====


@dataclass
class Address:
    """Level 3 nesting."""

    street_name: str
    post_code: str

    class Meta:
        key_transform_with_load = {
            "streetName": "street_name",
            "postCode": "post_code",
        }
        key_transform_with_dump = {
            "street_name": "streetName",
            "post_code": "postCode",
        }


@dataclass
class ContactInfo:
    """Level 2 nesting."""

    email_address: str
    phone_number: str
    home_address: Address

    class Meta:
        key_transform_with_load = {
            "emailAddress": "email_address",
            "phoneNumber": "phone_number",
            "homeAddress": "home_address",
        }
        key_transform_with_dump = {
            "email_address": "emailAddress",
            "phone_number": "phoneNumber",
            "home_address": "homeAddress",
        }


@dataclass
class UserProfile:
    """Level 1 nesting."""

    user_id: int
    full_name: str
    contact_details: ContactInfo

    class Meta:
        key_transform_with_load = {
            "userId": "user_id",
            "fullName": "full_name",
            "contactDetails": "contact_details",
        }
        key_transform_with_dump = {
            "user_id": "userId",
            "full_name": "fullName",
            "contact_details": "contactDetails",
        }


@dataclass
class OrganizationResponse:
    """Root level - 4 levels deep total."""

    org_name: str
    admin_profile: UserProfile

    class Meta:
        key_transform_with_load = {
            "orgName": "org_name",
            "adminProfile": "admin_profile",
        }
        key_transform_with_dump = {
            "org_name": "orgName",
            "admin_profile": "adminProfile",
        }


def test_structure_from_dict__deeply_nested_objects__structures_correctly():
    """
    Test structuring deeply nested objects (4 levels deep).

    Scenario:
        Real-world APIs often have deeply nested response structures.
        All levels must have proper camelCase → snake_case transformation.

    Expected Outcome:
        All nested levels are structured correctly with field name transformations
        applied at every level.
    """
    # Arrange: 4 levels deep: Organization → UserProfile → ContactInfo → Address
    json_response = {
        "orgName": "Acme Corp",
        "adminProfile": {
            "userId": 42,
            "fullName": "Jane Doe",
            "contactDetails": {
                "emailAddress": "jane@acme.com",
                "phoneNumber": "+1234567890",
                "homeAddress": {"streetName": "123 Main St", "postCode": "12345"},
            },
        },
    }

    # Act
    result = structure_from_dict(json_response, OrganizationResponse)

    # Assert: Verify all 4 levels
    assert isinstance(result, OrganizationResponse)
    assert result.org_name == "Acme Corp"

    assert isinstance(result.admin_profile, UserProfile)
    assert result.admin_profile.user_id == 42
    assert result.admin_profile.full_name == "Jane Doe"

    assert isinstance(result.admin_profile.contact_details, ContactInfo)
    assert result.admin_profile.contact_details.email_address == "jane@acme.com"
    assert result.admin_profile.contact_details.phone_number == "+1234567890"

    assert isinstance(result.admin_profile.contact_details.home_address, Address)
    assert result.admin_profile.contact_details.home_address.street_name == "123 Main St"
    assert result.admin_profile.contact_details.home_address.post_code == "12345"


def test_unstructure_to_dict__deeply_nested_objects__unstructures_correctly():
    """
    Test unstructuring deeply nested objects back to JSON.

    Scenario:
        Python dataclass with 4 levels of nesting needs to be serialised
        back to JSON with camelCase keys at all levels.

    Expected Outcome:
        All nested levels have field names transformed to camelCase.
    """
    # Arrange
    org = OrganizationResponse(
        org_name="Acme Corp",
        admin_profile=UserProfile(
            user_id=42,
            full_name="Jane Doe",
            contact_details=ContactInfo(
                email_address="jane@acme.com",
                phone_number="+1234567890",
                home_address=Address(street_name="123 Main St", post_code="12345"),
            ),
        ),
    )

    # Act
    result = unstructure_to_dict(org)

    # Assert: Verify all 4 levels have camelCase keys
    assert result["orgName"] == "Acme Corp"
    assert result["adminProfile"]["userId"] == 42
    assert result["adminProfile"]["fullName"] == "Jane Doe"
    assert result["adminProfile"]["contactDetails"]["emailAddress"] == "jane@acme.com"
    assert result["adminProfile"]["contactDetails"]["phoneNumber"] == "+1234567890"
    assert result["adminProfile"]["contactDetails"]["homeAddress"]["streetName"] == "123 Main St"
    assert result["adminProfile"]["contactDetails"]["homeAddress"]["postCode"] == "12345"


# ===== Test 3: Arrays within Objects within Arrays =====


@dataclass
class Tag:
    """Simple tag model."""

    tag_name: str

    class Meta:
        key_transform_with_load = {"tagName": "tag_name"}
        key_transform_with_dump = {"tag_name": "tagName"}


@dataclass
class Comment:
    """Comment with array of tags."""

    comment_id: int
    comment_text: str
    comment_tags: List[Tag] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "commentId": "comment_id",
            "commentText": "comment_text",
            "commentTags": "comment_tags",
        }
        key_transform_with_dump = {
            "comment_id": "commentId",
            "comment_text": "commentText",
            "comment_tags": "commentTags",
        }


@dataclass
class Post:
    """Post with array of comments (which each have array of tags)."""

    post_id: int
    post_title: str
    post_comments: List[Comment] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "postId": "post_id",
            "postTitle": "post_title",
            "postComments": "post_comments",
        }
        key_transform_with_dump = {
            "post_id": "postId",
            "post_title": "postTitle",
            "post_comments": "postComments",
        }


@dataclass
class BlogResponse:
    """Root with array of posts."""

    blog_posts: List[Post] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {"blogPosts": "blog_posts"}
        key_transform_with_dump = {"blog_posts": "blogPosts"}


def test_structure_from_dict__arrays_within_arrays__structures_correctly():
    """
    Test structuring arrays within objects within arrays (complex nesting).

    Scenario:
        Complex API response: Array of posts, each with array of comments,
        each comment with array of tags. Tests multiple levels of array nesting
        combined with object nesting.

    Expected Outcome:
        All nested arrays and objects are structured correctly with proper
        field name transformations at every level.
    """
    # Arrange: blogPosts[] → postComments[] → commentTags[]
    json_response = {
        "blogPosts": [
            {
                "postId": 1,
                "postTitle": "First Post",
                "postComments": [
                    {
                        "commentId": 101,
                        "commentText": "Great post!",
                        "commentTags": [{"tagName": "positive"}, {"tagName": "feedback"}],
                    },
                    {
                        "commentId": 102,
                        "commentText": "Thanks for sharing",
                        "commentTags": [{"tagName": "appreciation"}],
                    },
                ],
            },
            {
                "postId": 2,
                "postTitle": "Second Post",
                "postComments": [
                    {
                        "commentId": 201,
                        "commentText": "Interesting",
                        "commentTags": [{"tagName": "insight"}],
                    }
                ],
            },
        ]
    }

    # Act
    result = structure_from_dict(json_response, BlogResponse)

    # Assert: Verify structure at all levels
    assert isinstance(result, BlogResponse)
    assert len(result.blog_posts) == 2

    # First post
    first_post = result.blog_posts[0]
    assert isinstance(first_post, Post)
    assert first_post.post_id == 1
    assert first_post.post_title == "First Post"
    assert len(first_post.post_comments) == 2

    # First comment of first post
    first_comment = first_post.post_comments[0]
    assert isinstance(first_comment, Comment)
    assert first_comment.comment_id == 101
    assert first_comment.comment_text == "Great post!"
    assert len(first_comment.comment_tags) == 2

    # Tags of first comment
    assert isinstance(first_comment.comment_tags[0], Tag)
    assert first_comment.comment_tags[0].tag_name == "positive"
    assert first_comment.comment_tags[1].tag_name == "feedback"

    # Second post
    second_post = result.blog_posts[1]
    assert second_post.post_id == 2
    assert len(second_post.post_comments) == 1
    assert second_post.post_comments[0].comment_id == 201


# ===== Test 4: Union Types =====


@dataclass
class SuccessResponse:
    """Success response variant."""

    status: str
    result_data: str

    class Meta:
        key_transform_with_load = {"resultData": "result_data"}
        key_transform_with_dump = {"result_data": "resultData"}


@dataclass
class ErrorResponse:
    """Error response variant."""

    status: str
    error_message: str

    class Meta:
        key_transform_with_load = {"errorMessage": "error_message"}
        key_transform_with_dump = {"error_message": "errorMessage"}


def test_structure_from_dict__union_types__structures_success_correctly():
    """
    Test structuring union types (response can be one of multiple types).

    Scenario:
        API can return different response types based on success/failure.
        The client needs to handle Union[SuccessResponse, ErrorResponse].

    Expected Outcome:
        Correct dataclass type is structured based on JSON structure.
    """
    # Arrange: Success response
    json_success = {"status": "success", "resultData": "operation completed"}

    # Act
    result = structure_from_dict(json_success, SuccessResponse)

    # Assert
    assert isinstance(result, SuccessResponse)
    assert result.status == "success"
    assert result.result_data == "operation completed"


def test_structure_from_dict__union_types__structures_error_correctly():
    """
    Test structuring union type error variant.

    Scenario:
        API returns error response with different structure.

    Expected Outcome:
        Error response is structured correctly.
    """
    # Arrange: Error response
    json_error = {"status": "error", "errorMessage": "something went wrong"}

    # Act
    result = structure_from_dict(json_error, ErrorResponse)

    # Assert
    assert isinstance(result, ErrorResponse)
    assert result.status == "error"
    assert result.error_message == "something went wrong"


# ===== Test 5: Enums =====


class StatusEnum(str, Enum):
    """Status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


@dataclass
class AccountStatus:
    """Account with enum status."""

    account_id: int
    account_status: StatusEnum

    class Meta:
        key_transform_with_load = {
            "accountId": "account_id",
            "accountStatus": "account_status",
        }
        key_transform_with_dump = {
            "account_id": "accountId",
            "account_status": "accountStatus",
        }


def test_structure_from_dict__enum_values__structures_correctly():
    """
    Test structuring enum values from JSON strings.

    Scenario:
        API returns enum values as strings that need to be converted to Python Enums.

    Expected Outcome:
        JSON string values are correctly converted to Enum instances.
    """
    # Arrange
    json_response = {"accountId": 123, "accountStatus": "active"}

    # Act
    result = structure_from_dict(json_response, AccountStatus)

    # Assert
    assert isinstance(result, AccountStatus)
    assert result.account_id == 123
    assert result.account_status == StatusEnum.ACTIVE
    assert isinstance(result.account_status, StatusEnum)


def test_unstructure_to_dict__enum_values__unstructures_correctly():
    """
    Test unstructuring enum values back to JSON strings.

    Scenario:
        Python Enum instances need to be serialised as string values in JSON.

    Expected Outcome:
        Enum instances are converted to their string values.
    """
    # Arrange
    account = AccountStatus(account_id=123, account_status=StatusEnum.INACTIVE)

    # Act
    result = unstructure_to_dict(account)

    # Assert
    assert result["accountId"] == 123
    assert result["accountStatus"] == "inactive"
    assert isinstance(result["accountStatus"], str)


# ===== Test 6: Edge Cases =====


@dataclass
class EdgeCaseModel:
    """Model with various edge case fields."""

    empty_string: str
    zero_value: int
    false_boolean: bool
    null_optional: str | None = None

    class Meta:
        key_transform_with_load = {
            "emptyString": "empty_string",
            "zeroValue": "zero_value",
            "falseBoolean": "false_boolean",
            "nullOptional": "null_optional",
        }
        key_transform_with_dump = {
            "empty_string": "emptyString",
            "zero_value": "zeroValue",
            "false_boolean": "falseBoolean",
            "null_optional": "nullOptional",
        }


def test_structure_from_dict__edge_case_values__handles_correctly():
    """
    Test handling of edge case values (empty strings, zeros, false, null).

    Scenario:
        JSON can contain edge case values that might be mishandled (empty strings,
        zero, false, null). These should not be confused with missing values.

    Expected Outcome:
        Edge case values are preserved correctly, distinct from defaults.
    """
    # Arrange
    json_response = {
        "emptyString": "",
        "zeroValue": 0,
        "falseBoolean": False,
        "nullOptional": None,
    }

    # Act
    result = structure_from_dict(json_response, EdgeCaseModel)

    # Assert
    assert result.empty_string == ""  # Not None or missing
    assert result.zero_value == 0  # Not None or missing
    assert result.false_boolean is False  # Not None or missing
    assert result.null_optional is None  # Explicitly None


@dataclass
class MixedCaseModel:
    """Model where some fields don't need transformation."""

    name: str  # Already snake_case, maps to "name"
    user_age: int  # snake_case, maps to "userAge"
    email: str  # Single word, maps to "email"

    class Meta:
        key_transform_with_load = {"userAge": "user_age"}
        key_transform_with_dump = {"user_age": "userAge"}


def test_structure_from_dict__mixed_case_fields__handles_correctly():
    """
    Test handling fields where some need transformation and some don't.

    Scenario:
        Not all JSON keys are camelCase - some might already match Python conventions
        or be single words. The converter should handle mixed scenarios.

    Expected Outcome:
        Fields that need transformation are transformed, others pass through unchanged.
    """
    # Arrange
    json_response = {
        "name": "John",  # No transformation needed
        "userAge": 30,  # Needs transformation to user_age
        "email": "john@example.com",  # No transformation needed
    }

    # Act
    result = structure_from_dict(json_response, MixedCaseModel)

    # Assert
    assert result.name == "John"
    assert result.user_age == 30
    assert result.email == "john@example.com"


@dataclass
class EmptyCollectionsModel:
    """Model with empty collections."""

    empty_list: List[str] = field(default_factory=list)
    empty_nested_list: List[Tag] = field(default_factory=list)

    class Meta:
        key_transform_with_load = {
            "emptyList": "empty_list",
            "emptyNestedList": "empty_nested_list",
        }
        key_transform_with_dump = {
            "empty_list": "emptyList",
            "empty_nested_list": "emptyNestedList",
        }


def test_structure_from_dict__empty_collections__handles_correctly():
    """
    Test handling of empty arrays at various nesting levels.

    Scenario:
        JSON can contain empty arrays which should be converted to empty Python lists.

    Expected Outcome:
        Empty JSON arrays become empty Python lists, not None.
    """
    # Arrange
    json_response = {"emptyList": [], "emptyNestedList": []}

    # Act
    result = structure_from_dict(json_response, EmptyCollectionsModel)

    # Assert
    assert result.empty_list == []
    assert result.empty_nested_list == []
    assert isinstance(result.empty_list, list)
    assert isinstance(result.empty_nested_list, list)
