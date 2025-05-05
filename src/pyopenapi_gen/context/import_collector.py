# HACK START: Explicitly remove the problematic key before formatting
# if "..models.union_agent_response_dict_str_any" in self.relative_imports:
#     del self.relative_imports["..models.union_agent_response_dict_str_any"]
#     print("DEBUG [get_import_statements]: HACK Applied - Removed '..models.union_agent_response_dict_str_any' key.", file=sys.stderr)
# HACK END

# Format relative imports
for module, names_set in self.relative_imports.items():
    if not names_set:
        continue  # Skip if no names were actually added
    sorted_names = sorted(list(names_set))
