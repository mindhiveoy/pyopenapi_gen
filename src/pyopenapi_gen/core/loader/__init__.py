"""Loader package to transform OpenAPI specs into Intermediate Representation.

This package contains the classes and functions to load OpenAPI specifications
and transform them into the internal IR dataclasses, which are then used for
code generation.
"""

from __future__ import annotations

from .loader import SpecLoader, load_ir_from_spec

__all__ = ["SpecLoader", "load_ir_from_spec"]
