# Claude GitHub App Configuration

This document explains the Claude GitHub App configuration for automatic PR reviews and approvals.

## Configuration Files

### 1. `claude.yml` - Main Claude Workflow
- **Triggers**: @claude mentions in comments, PR events
- **Permissions**: Full write access to contents, PRs, issues
- **Features**: 
  - Automatic formal PR reviews (`create_review: true`)
  - Auto-approval capability (`auto_approve: true`)
  - Extended tool access for PR management

### 2. `claude-review-trigger.yml` - Automatic Review Notifications
- **Triggers**: PRs opened/updated on develop, staging, main
- **Scope**: 
  - All PRs targeting protected branches
  - Dependabot PRs
  - Release/fix/chore PRs from devops-mindhive
  - PRs with `[claude-review]` tag
- **Action**: Posts @claude mention to trigger review

### 3. `claude-auto-approve.yml` - Formal Approval Workflow  
- **Triggers**: Claude review submissions with APPROVE/APPROVED
- **Features**:
  - Creates formal GitHub PR approvals
  - Auto-merge capability for qualifying PRs
  - Safety checks for merge readiness

## Required Repository Setup

### Secrets
- ✅ `ANTHROPIC_API_KEY` - Configured in repository secrets

### Permissions
The Claude GitHub App has these permissions:
- ✅ `contents: write` - Modify files and commit changes
- ✅ `pull-requests: write` - Review, approve, and merge PRs  
- ✅ `issues: write` - Create and manage issues
- ✅ `actions: read` - Monitor CI/CD status
- ✅ `checks: read` - Review test results
- ✅ `statuses: read` - Check status checks

## How It Works

### Automatic Workflow
1. **PR Created** → `claude-review-trigger.yml` posts @claude mention
2. **Claude Triggered** → `claude.yml` runs comprehensive review
3. **Review Complete** → Claude provides formal GitHub approval
4. **Auto-Merge** → `claude-auto-approve.yml` merges if all checks pass

### Manual Workflow  
1. **Comment @claude** on any PR or issue
2. **Claude Responds** with review, fixes, or approvals as needed
3. **Formal Actions** taken based on Claude's assessment

## Branch Protection Compatibility

The configuration works with branch protection rules requiring:
- ✅ **Status Checks**: All CI must pass
- ✅ **Required Reviews**: Claude provides formal GitHub approvals
- ✅ **Up-to-date Branch**: Auto-handled by merge process

## Troubleshooting

### Claude Not Responding to @mentions
- Check `claude.yml` workflow is enabled
- Verify triggers include your PR's target branch
- Ensure ANTHROPIC_API_KEY secret is valid

### Reviews Not Counting as Approvals
- Confirm `create_review: true` in claude.yml
- Check that `claude-auto-approve.yml` is processing Claude's reviews
- Verify branch protection accepts app reviews

### Auto-Merge Not Working
- Ensure all required status checks pass
- Check PR is marked as mergeable
- Verify `auto_approve: true` is enabled

## Testing

To test the configuration:
1. Create a test PR with `[claude-review]` tag
2. Comment `@claude please review this PR`
3. Verify Claude provides formal approval
4. Check if auto-merge occurs (if enabled)