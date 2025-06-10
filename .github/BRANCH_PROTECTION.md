# Branch Protection Configuration

This document outlines the required GitHub branch protection settings for the `develop` branch.

## Required Settings

### Branch Protection Rules for `develop`

1. **Require pull request reviews before merging**
   - Required approving reviews: 1
   - Dismiss stale reviews when new commits are pushed: ✅
   - Require review from code owners: ✅ (if CODEOWNERS file exists)

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   - Required status checks:
     - `quality-checks (3.10)`
     - `quality-checks (3.11)` 
     - `quality-checks (3.12)`
     - `security-scan`
     - `integration-tests`

3. **Require conversation resolution before merging**: ✅

4. **Require signed commits**: ❌ (optional)

5. **Require linear history**: ❌ (optional)

6. **Do not allow bypassing the above settings**: ✅

7. **Restrict pushes that create files**: ❌

8. **Allow force pushes**: ❌

9. **Allow deletions**: ❌

## How to Configure

### Via GitHub Web Interface

1. Go to your repository on GitHub
2. Click on **Settings** → **Branches**
3. Click **Add rule** or edit existing rule for `develop`
4. Configure the settings as outlined above
5. Save the branch protection rule

### Via GitHub CLI (if available)

```bash
# Example command (adjust as needed)
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality-checks (3.10)","quality-checks (3.11)","quality-checks (3.12)","security-scan","integration-tests"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

## Quality Gates Enforced

The pipeline enforces the following quality gates:

### Code Quality
- ✅ **Black formatting**: Code must be properly formatted
- ✅ **Ruff linting**: No linting errors allowed
- ✅ **MyPy type checking**: Strict type checking must pass

### Testing
- ✅ **Unit tests**: All tests must pass
- ✅ **Integration tests**: End-to-end functionality verified
- ✅ **Coverage**: Minimum 90% test coverage required
- ✅ **Multi-Python version**: Tests on Python 3.10, 3.11, 3.12

### Security
- ✅ **Safety check**: No known vulnerabilities in dependencies
- ✅ **Bandit scan**: Security linting for common issues

### Functionality
- ✅ **CLI functionality**: Command-line interface works correctly
- ✅ **Client generation**: Generated clients have proper structure
- ✅ **Package building**: Project can be built successfully

## Workflow Files

- `.github/workflows/pr-checks.yml`: Runs on PRs to develop branch
- `.github/workflows/main-checks.yml`: Runs on pushes to main branch

## Local Development

Before creating a PR, run locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run quality checks
black src/ tests/
ruff check src/ tests/
mypy src/ --strict --no-warn-no-return

# Run tests
pytest --cov=src --cov-report=term-missing --cov-fail-under=90

# Test CLI
pyopenapi-gen --help
```

This ensures your PR will pass the automated checks.