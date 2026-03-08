"""
Tests for the module-level caching and hook-priority behaviour in cattrs_converter.py.

Covers:
- _get_type_hints_with_extras falls back to {} without propagating exceptions
- _structure_hooks_registered prevents re-registration across repeated calls (O(N) total)
- User-registered exact hooks are not overwritten by our lower-priority predicate hooks
- _unstructure_fn_cache is populated lazily on first call and reused thereafter
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest

from pyopenapi_gen.core import cattrs_converter as cc
from pyopenapi_gen.core.cattrs_converter import structure_from_dict, unstructure_to_dict

# ---------------------------------------------------------------------------
# _get_type_hints_with_extras
# ---------------------------------------------------------------------------


def test_get_type_hints_with_extras__unresolvable_annotation__returns_empty_dict():
    """
    Scenario:
        A class has a string annotation that cannot be resolved (missing type in scope).

    Expected Outcome:
        _get_type_hints_with_extras returns {} without raising and caches the empty result.
    """

    class BrokenAnnotations:
        __annotations__ = {"field": "ThisTypeCannotBeResolved_xyzABC"}
        __module__ = "_nonexistent_module_xyz"

    # Arrange: ensure clean cache state
    cc._type_hints_cache.pop(BrokenAnnotations, None)

    # Act
    result = cc._get_type_hints_with_extras(BrokenAnnotations)

    # Assert: graceful fallback and cached
    assert result == {}
    assert cc._type_hints_cache[BrokenAnnotations] == {}

    # Cleanup
    cc._type_hints_cache.pop(BrokenAnnotations, None)


def test_get_type_hints_with_extras__valid_class__result_cached():
    """
    Scenario:
        A normal class is passed twice.

    Expected Outcome:
        The second call returns the cached dict without invoking get_type_hints again.
    """

    @dataclass
    class CacheHit:
        value: int

    cc._type_hints_cache.pop(CacheHit, None)

    with patch("pyopenapi_gen.core.cattrs_converter.get_type_hints", wraps=cc.get_type_hints) as mock_gth:
        cc._get_type_hints_with_extras(CacheHit)
        first_count = mock_gth.call_count

        cc._get_type_hints_with_extras(CacheHit)

        # No additional calls on cache hit
        assert mock_gth.call_count == first_count

    # Cleanup
    cc._type_hints_cache.pop(CacheHit, None)


# ---------------------------------------------------------------------------
# _structure_hooks_registered — O(N) registration guard
# ---------------------------------------------------------------------------


def test_structure_registration__repeated_structure_calls__hook_built_only_once():
    """
    Scenario:
        structure_from_dict is called 10 times with the same dataclass.

    Expected Outcome:
        _make_dataclass_structure_fn is called exactly once; subsequent calls
        return early via _structure_hooks_registered without rebuilding the hook.
    """

    @dataclass
    class RepeatStructure:
        x: int

    data = {"x": 1}

    with patch(
        "pyopenapi_gen.core.cattrs_converter._make_dataclass_structure_fn",
        wraps=cc._make_dataclass_structure_fn,
    ) as mock_build:
        structure_from_dict(data, RepeatStructure)
        calls_after_first = mock_build.call_count

        for _ in range(9):
            structure_from_dict(data, RepeatStructure)

        assert (
            mock_build.call_count == calls_after_first
        ), "_make_dataclass_structure_fn must not be called again after initial registration"

    # Cleanup
    cc._structure_hooks_registered.discard(RepeatStructure)
    cc._type_hints_cache.pop(RepeatStructure, None)


# ---------------------------------------------------------------------------
# Hook priority: user exact hooks must survive predicate registration
# ---------------------------------------------------------------------------


def test_user_exact_structure_hook__not_overwritten_by_predicate_hook():
    """
    Scenario:
        A custom exact hook is registered via converter.register_structure_hook
        before structure_from_dict is called. Our code registers a predicate hook
        (lower priority) for the same class.

    Expected Outcome:
        The exact hook wins; its return value (value × 10 sentinel) is used,
        not the predicate hook (value as-is).
    """

    @dataclass
    class GuardedStructure:
        value: int

    calls: list[Any] = []

    def custom_hook(data: dict, _type: type) -> GuardedStructure:
        calls.append(data)
        return GuardedStructure(value=data["value"] * 10)  # sentinel

    # Arrange: register exact hook first
    cc.converter.register_structure_hook(GuardedStructure, custom_hook)

    # Act: triggers predicate hook registration (lower priority)
    result = structure_from_dict({"value": 3}, GuardedStructure)

    # Assert: custom exact hook ran, not our generic predicate hook
    assert result.value == 30, (
        f"Expected 30 (custom hook: value×10), got {result.value}. "
        "Our predicate hook must not override user-registered exact hooks."
    )
    assert len(calls) == 1

    # Cleanup
    cc._structure_hooks_registered.discard(GuardedStructure)
    cc._type_hints_cache.pop(GuardedStructure, None)


def test_user_exact_unstructure_hook__not_overwritten_by_predicate_hook():
    """
    Scenario:
        A custom exact unstructure hook is registered before unstructure_to_dict is called.

    Expected Outcome:
        The exact hook wins; its return value (value × 10 sentinel) is used.
    """

    @dataclass
    class GuardedUnstructure:
        value: int

    calls: list[Any] = []

    def custom_hook(obj: GuardedUnstructure) -> dict:
        calls.append(obj)
        return {"value": obj.value * 10}  # sentinel

    # Arrange: register exact hook first
    cc.converter.register_unstructure_hook(GuardedUnstructure, custom_hook)

    # Act: triggers predicate hook registration (lower priority)
    result = unstructure_to_dict(GuardedUnstructure(value=5))

    # Assert: custom exact hook ran
    assert result["value"] == 50, (
        f"Expected 50 (custom hook: value×10), got {result['value']}. "
        "Our predicate hook must not override user-registered exact hooks."
    )
    assert len(calls) == 1

    # Cleanup
    cc._unstructure_hooks_registered.discard(GuardedUnstructure)
    cc._unstructure_fn_cache.pop(GuardedUnstructure, None)
    cc._type_hints_cache.pop(GuardedUnstructure, None)


# ---------------------------------------------------------------------------
# _unstructure_fn_cache — lazy build, then reuse
# ---------------------------------------------------------------------------


def test_unstructure_fn_cache__populated_on_first_call__reused_on_second():
    """
    Scenario:
        unstructure_to_dict is called twice for the same class.

    Expected Outcome:
        _make_dataclass_unstructure_fn is called exactly once (first invocation
        of the hook closure). The second call uses the cached function.
    """

    @dataclass
    class LazyUnstructure:
        name: str

        class Meta:
            key_transform_with_load = {"name": "name"}
            key_transform_with_dump = {"name": "name"}

    instance = LazyUnstructure(name="hello")

    # Arrange: clean state
    cc._unstructure_fn_cache.pop(LazyUnstructure, None)
    cc._unstructure_hooks_registered.discard(LazyUnstructure)

    # First call: cache miss → _make_dataclass_unstructure_fn is invoked
    assert LazyUnstructure not in cc._unstructure_fn_cache

    unstructure_to_dict(instance)

    assert LazyUnstructure in cc._unstructure_fn_cache

    # Second call: cache hit → _make_dataclass_unstructure_fn must NOT be called again
    with patch(
        "pyopenapi_gen.core.cattrs_converter._make_dataclass_unstructure_fn",
        wraps=cc._make_dataclass_unstructure_fn,
    ) as mock_build:
        result = unstructure_to_dict(instance)
        assert mock_build.call_count == 0, "_make_dataclass_unstructure_fn must not be called when result is cached"

    assert result == {"name": "hello"}

    # Cleanup
    cc._unstructure_fn_cache.pop(LazyUnstructure, None)
    cc._unstructure_hooks_registered.discard(LazyUnstructure)
    cc._type_hints_cache.pop(LazyUnstructure, None)


# ---------------------------------------------------------------------------
# structure_fn — non-dict, non-None input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_input, expected_type_name",
    [
        (42, "int"),
        ([1, 2], "list"),
        (3.14, "float"),
    ],
)
def test_structure_fn__non_dict_input__raises_type_error_with_type_name(bad_input: Any, expected_type_name: str):
    """
    Scenario:
        structure_from_dict receives a non-dict, non-None value for a dataclass target.

    Expected Outcome:
        ValueError is raised; the message names the received type so the caller
        knows what kind of data arrived.
    """

    @dataclass
    class SimpleTarget:
        value: int

    with pytest.raises(ValueError, match=expected_type_name):
        structure_from_dict(bad_input, SimpleTarget)
