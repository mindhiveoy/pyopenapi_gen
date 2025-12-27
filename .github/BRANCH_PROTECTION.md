# Branch Protection Configuration

This document outlines the GitHub branch protection settings for the `develop`, `staging`, and `main` branches.

## 🛡️ Branch Protection Status

All three critical branches are now **FULLY PROTECTED** with the following settings:

- **main**: ✅ Protected with full CI/CD enforcement
- **staging**: ✅ Protected with full CI/CD enforcement  
- **develop**: ✅ Protected with full CI/CD enforcement

## Required Settings

### Branch Protection Rules for `develop`, `staging`, and `main`

1. **Require pull request reviews before merging**
   - Required approving reviews: 1
   - Dismiss stale reviews when new commits are pushed: ✅
   - Require review from code owners: ✅ (if CODEOWNERS file exists)

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   - Required status checks:
     - `format-check` (Black formatting)
     - `lint` (Ruff linting)
     - `typecheck` (MyPy type checking)
     - `security` (Bandit security scanning)
     - `test` (Full test suite with 85% coverage)

3. **Require conversation resolution before merging**: ✅

4. **Require signed commits**: ❌ (optional)

5. **Require linear history**: ❌ (optional)

6. **Do not allow bypassing the above settings**: ✅

7. **Restrict pushes that create files**: ❌

8. **Allow force pushes**: ❌

9. **Allow deletions**: ❌

## 🔒 Protection Features

### Deletion Protection
All branches are protected from accidental deletion:
- Force pushes are disabled
- Branch deletion is explicitly forbidden
- Admin privileges still enforce protection rules

### Quality Gates
Every PR must pass all quality checks:
- Code formatting (Black)
- Linting (Ruff) 
- Type checking (MyPy strict mode)
- Security scanning (Bandit)
- Test suite with 85% coverage minimum

## How to Configure

### Via GitHub Web Interface

1. Go to your repository on GitHub
2. Click on **Settings** → **Branches**
3. Click **Add rule** or edit existing rule for `develop`
4. Configure the settings as outlined above
5. Save the branch protection rule

### Via GitHub CLI

The protection was applied using GitHub CLI. Here's how to configure each branch:

```bash
# Create protection JSON
cat > branch_protection.json << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["format-check", "lint", "typecheck", "security", "test"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_deletions": false,
  "allow_force_pushes": false
}
EOF

# Apply to each branch
gh api --method PUT repos/OWNER/REPO/branches/main/protection --input branch_protection.json
gh api --method PUT repos/OWNER/REPO/branches/develop/protection --input branch_protection.json
gh api --method PUT repos/OWNER/REPO/branches/staging/protection --input branch_protection.json
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
- ✅ **Coverage**: Minimum 85% test coverage required
- ✅ **Python version**: Tests on Python 3.12+

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

Before creating a PR, run locally to ensure it will pass CI:

```bash
# Activate virtual environment
source .venv/bin/activate

# Auto-fix what's possible
make quality-fix

# Verify all quality gates pass (exactly matches CI pipeline)
make quality

# Run tests with coverage
make test-cov
```

### Individual Commands (if needed)

```bash
# Quality checks (matches CI pipeline exactly)
make format-check         # Black formatting check
make lint                 # Ruff linting check  
make typecheck            # mypy type checking
make security             # Bandit security scanning

# Testing
make test                 # Run all tests
make test-fast            # Stop on first failure (for debugging)

# Auto-fixes
make format               # Auto-format with Black
make lint-fix             # Auto-fix linting with Ruff
```

### Why Use Make Commands?

The `make` commands ensure you're running **exactly** the same checks as the CI pipeline. This prevents the "works locally but fails in CI" problem and provides fast feedback during development.