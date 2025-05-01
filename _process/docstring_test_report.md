# Docstring Rendering Test Failure Report

## Summary

8 tests failed in `tests/core/writers/test_documentation_writer.py`. All failures are related to the Args section formatting (alignment, padding, wrapping, and special cases). Below is a breakdown of each failure, the expected vs. actual output, and the likely root cause.

---

# Failing Test Alignment Summary

Below are the failing tests, with expected and actual output shown alongside a column ruler. The colon and description columns are marked for clarity.

```python
## Ruler (Columns 1–50)
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
# C = colon, D = description start
```
---

### 1. `test_render_docstring__args_section__renders_args_with_types_and_desc`
**Checks:** Alignment and wrapping of multiple arguments in Args section.

**Expected:**
```python
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    foo (int)                : The foo parameter.
    bar (str)                : A longer description that should wrap to the
                               next line for readability.
```
**Actual:**
```python
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    foo (int)           : The foo parameter.
    bar (str)           : A longer description
                          that should wrap to the
                          next line for
                          readability.
```
**Note:** Colon and description are not at the expected columns; too little padding before the colon, wrapped lines not aligned to column 36.

**Root Cause:** Padding calculation is off; wrapping logic may be using a narrower width or not aligning wrapped lines to the correct column.

---

### 2. `test_render_docstring__all_sections__renders_full_docstring`
**Checks:** All sections, especially Args alignment.

**Expected:**
```python
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    x (int)                  : First param.
    y (str)                  : Second param.
```
**Actual:**
```python
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    x (int)                       : First param.
    y (str)                       : Second param.
```
**Note:** Colon and description are not at the expected columns; too much padding before the colon.

**Root Cause:** Args alignment logic is not matching the expected min_desc_col.

---

### 3. `test_render_docstring__arg_prefix_longer_than_desc_col__colon_and_space_on_next_line`
**Checks:** Long argument prefix, colon on its own line, description starts on next line, indented to match colon.

**Expected:**
```python
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    averyveryverylongargumentnameindeed (str)
                                 : Description for a very long argument name.
```
**Actual:**
```python
#    1         2         3         4         5
#        1         2         3         4         5
# 3456789012345678901234567890123456789012345678901234567890
#                            C D
    averyveryverylongargumentnameindeed (str):
                     Description for a very long
                     argument name.
```
**Note:** Colon is not on its own line, and description is not indented to the correct column.

**Root Cause:** For long prefixes, the colon should be on its own line, and the description should be indented to the same column as the colon, not just desc_col+1.

---

### 4. `test_render_docstring__arg_with_empty_description__renders_colon_only`
**Checks:** Arg with empty description, should end with colon and no extra spaces.

**Expected:**
```python
"""
Empty desc.

Args:
    foo (int)         :
"""
```
**Actual:**
```python
"""
Empty desc.

Args:
    foo (int)           :
"""
```
**Root Cause:** Padding calculation is off for empty descriptions.

---

### 5. `test_render_docstring__arg_with_multiline_description__all_lines_aligned`
**Checks:** Multiline description, all lines should be aligned under the colon.

**Expected:**
```python
"""
Multiline desc.

Args:
    foo (str)         : This is a long description.
                        It has multiple lines.
                        Each should be aligned.
"""
```
**Actual:**
```python
"""
Multiline desc.

Args:
    foo (str)           : This is a long
                          description.
                         It has multiple lines.
                         Each should be aligned.
"""
```
**Root Cause:** Padding and wrapping logic for multiline descriptions is not matching the expected alignment.

---

### 6. `test_render_docstring__arg_prefix_with_unicode__renders_colon_and_space`
**Checks:** Unicode argument name, colon and space alignment.

**Expected:**
```python
"""
Unicode prefix.

Args:
    tên (str)   : Unicode argument name.
"""
```
**Actual:**
```python
"""
Unicode prefix.

Args:
    tên (str)      : Unicode argument
                     name.
"""
```
**Root Cause:** Padding and alignment logic does not handle unicode or short prefixes correctly.

---

### 7. `test_render_docstring__arg_prefix_with_special_characters__renders_colon_and_space`
**Checks:** Special characters in argument name, colon and space alignment.

**Expected:**
```python
"""
Special chars.

Args:
    foo-bar_baz (str) : Special chars in name.
"""
```
**Actual:**
```python
"""
Special chars.

Args:
    foo-bar_baz (str):
                Special chars in name.
"""
```
**Root Cause:** Logic for short prefixes with special characters is not matching expected output.

---

### 8. `test_render_docstring__multiple_args__alignment_and_wrapping`
**Checks:** Multiple arguments, alignment and wrapping for each.

**Expected:**
```python
"""
Multiple args.

Args:
    foo (int)         : Short desc.
    bar (str)         : This is a long description that should wrap to the
                        next line for readability.
    baz (str)         : First line.
                        Second line of multiline desc.
                        Third line.
"""
```
**Actual:**
```python
"""
Multiple args.

Args:
    foo (int)           : Short desc.
    bar (str)           : This is a long description that
                          should wrap to the next line for
                          readability.
    baz (str)           : First line.
                         Second line of multiline desc.
                         Third line.
"""
```
**Root Cause:** General padding and wrapping logic for Args section needs to be tightened to match min_desc_col and expected alignment.

---

## General Root Cause
- The Args section renderer is adding too much padding before the colon for short prefixes, and not handling long prefixes (colon on its own line, description indented to match) as expected. Wrapping logic for multiline and wrapped lines is not aligning subsequent lines to the correct column.

## Next Steps
- Adjust the padding calculation for short prefixes to match exactly min_desc_col.
- For long prefixes, put the colon on its own line, and indent the description to the same column as the colon.
- Ensure all wrapped and multiline lines are aligned under the colon, not just desc_col+1. 