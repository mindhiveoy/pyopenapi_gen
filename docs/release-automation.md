# Release Automation with Semantic Versioning

## Overview

This project uses **semantic-release** to automatically bump versions, generate changelogs, and publish to PyPI based on conventional commit messages. This ensures that bug fixes and new features are automatically released to users without manual intervention.

## How It Works

### 1. Conventional Commits Trigger Releases

When you push commits to the `main` branch with conventional commit prefixes, they automatically trigger version bumps:

- `fix:` → Patch release (0.12.0 → 0.12.1)
- `feat:` → Minor release (0.12.0 → 0.13.0)
- `BREAKING CHANGE:` → Major release (0.12.0 → 1.0.0)

Other prefixes (`docs:`, `style:`, `refactor:`, `test:`, `chore:`) do not trigger releases.

### 2. Automatic Version Bumping

The GitHub Actions workflow (`semantic-release.yml`) runs on every push to main:

1. **Checks for release-worthy commits** since the last tag
2. **Runs semantic-release** to determine the next version
3. **Updates version** in:
   - `pyproject.toml` (project.version)
   - `pyproject.toml` (tool.commitizen.version)
   - `src/pyopenapi_gen/__init__.py` (__version__)
4. **Generates CHANGELOG.md** from commit messages
5. **Creates git tag** (e.g., v0.12.1)
6. **Commits changes** with message "chore(release): {version}"

### 3. Package Building and Publishing

After version bump:

1. **Builds packages** using `python -m build`
2. **Validates PyPI token** (PYPI_API_TOKEN secret)
3. **Publishes to PyPI** using twine
4. **Creates GitHub release** with changelog
5. **Syncs branches** (main → staging → develop)

## Example: The v0.12.1 Release

Here's how the v0.12.1 hotfix was automatically released:

### Step 1: Fix Was Committed
```bash
git commit -m "fix(parser): register inline enum array parameters in parsed_schemas

Critical fix for inline enum array parameters not generating importable model files.

Root cause:
- Inline enum schemas in array parameters were created but never registered
- Missing final_module_stem attribute prevented proper import generation  
- Generated clients failed with NameError when importing enum types

Solution:
- Register inline enum schemas in context.parsed_schemas
- Set final_module_stem for proper import path generation
- Add comprehensive test coverage for inline enum parameters

Impact:
- All inline enum array parameters now generate proper model files
- Generated clients can be imported without NameError
- Fixes business_swagger.json generation issues"
```

### Step 2: Push to Main Triggered Workflow
```bash
git push origin main
```

### Step 3: Automatic Processing
1. Workflow detected `fix:` commit since v0.12.0
2. Semantic-release bumped version to 0.12.1
3. Updated all version files
4. Generated changelog entry
5. Built and published to PyPI
6. Created GitHub release
7. Synced to staging and develop branches

### Step 4: Users Get Update
```bash
pip install --upgrade pyopenapi-gen
# Automatically gets v0.12.1 with the fix
```

## Configuration

### pyproject.toml
```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version", "pyproject.toml:tool.commitizen.version"]
version_pattern = [
    "src/pyopenapi_gen/__init__.py:__version__: str = \"{version}\""
]
branch = "main"
upload_to_pypi = false  # We use twine instead
upload_to_repository = false
commit_message = "chore(release): {version}"
tag_commit = true
changelog_file = "CHANGELOG.md"
hvcs = "github"
commit_parser = "conventional"
major_on_zero = false
```

### GitHub Secrets Required
- `PYPI_API_TOKEN`: PyPI token for publishing (starts with `pypi-`)
- `SEMANTIC_RELEASE_TOKEN` (optional): GitHub token with push permissions

## Best Practices

### 1. Write Clear Commit Messages
```bash
# Good - triggers patch release
fix(parser): resolve circular reference in schema parsing

# Good - triggers minor release  
feat(cli): add --dry-run option for testing

# Good - triggers major release
feat(api): redesign authentication system

BREAKING CHANGE: AuthPlugin interface changed
```

### 2. Group Related Changes
```bash
# Instead of multiple commits:
fix: update import
fix: handle None case
fix: add test

# Use one semantic commit:
fix(module): handle None values in import resolution

- Update import logic
- Add None value handling
- Add comprehensive tests
```

### 3. Non-Release Commits
```bash
# These don't trigger releases:
style: apply Black formatting
docs: update README
chore: update dependencies
test: add edge case coverage
refactor: simplify logic
```

## Troubleshooting

### Version Not Bumping?
1. Check commit has `fix:`, `feat:`, or `BREAKING CHANGE:`
2. Ensure pushing to `main` branch
3. Check workflow passed all quality gates
4. Verify no version conflict with PyPI

### Manual Release
```bash
# Trigger workflow manually from GitHub Actions UI
# Or use workflow_dispatch:
gh workflow run semantic-release.yml
```

### Check Release Status
```bash
# View recent workflow runs
gh run list --workflow=semantic-release.yml

# Check PyPI for latest version
curl -s https://pypi.org/pypi/pyopenapi-gen/json | jq .info.version

# Check git tags
git fetch --tags
git tag | tail -5
```

## Benefits

1. **Zero Manual Intervention**: Fix → Push → Released
2. **Consistent Versioning**: Follows semantic versioning strictly
3. **Automatic Changelog**: Generated from commit messages
4. **Immediate Availability**: Users get fixes within minutes
5. **Branch Synchronization**: All branches stay up-to-date
6. **Quality Gates**: Only releases if all tests pass

This automation ensures that critical fixes like the inline enum parameter issue are immediately available to users without waiting for manual release processes.