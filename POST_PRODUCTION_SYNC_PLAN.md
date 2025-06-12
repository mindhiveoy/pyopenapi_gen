# Post-Production Branch Sync Plan

## Objective
After v0.8.5 production release, ensure all branches have the latest fixes and are properly synchronized.

## Current Status (Post-Production)
- **main**: ✅ Has v0.8.5, CI fix, TestPyPI fix  
- **staging**: ❌ Missing CI fix, will have v0.8.5 content
- **develop**: ❌ Missing CI fix, missing latest production changes

## Required Actions

### 1. Sync Staging Branch
```bash
# staging ← main (get CI fix and any main-only changes)
git checkout staging
git pull origin staging
git merge origin/main  # Get CI workflow fix
git push origin staging
```

### 2. Sync Develop Branch  
```bash
# develop ← main (get all production changes)
git checkout develop
git pull origin develop  
git merge origin/main  # Get v0.8.5, CI fix, TestPyPI fix
git push origin develop
```

## Verification

### Branch State After Sync
- **main**: v0.8.5 production + all fixes
- **staging**: v0.8.5 production + all fixes (synced from main)
- **develop**: v0.8.5 production + all fixes (synced from main)

### Key Files to Verify
- `.github/workflows/ci.yml`: Should have `staging` in branches list
- `.github/workflows/testpypi-publish.yml`: Should trigger on `staging` 
- `pyproject.toml`: Should have version 0.8.5
- All ResponseStrategy improvements should be present

## Final Validation
- [ ] All branches can create PRs without protection rule issues
- [ ] CI workflows run on all protected branches
- [ ] Version consistency across branches
- [ ] TestPyPI publishes from staging pushes
- [ ] Production PyPI publishes from main tags

## Notes
- This sync ensures clean state for future development
- All branches will have identical workflow configurations
- Future PRs won't face protection rule mismatches