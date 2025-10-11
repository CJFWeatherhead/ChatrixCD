# GitHub Actions Workflows

This repository uses GitHub Actions for continuous integration and automated releases.

## Test Workflow (`test.yml`)

### Trigger Events
- Pull requests to `main` or `develop` branches
- Push to `main` branch

### What it does
1. Checks out the code
2. Sets up Python (versions 3.8, 3.9, 3.10, 3.11)
3. Installs dependencies
4. Runs all unit tests using `python -m unittest discover`

### How to use
The workflow runs automatically on pull requests and pushes. No manual intervention needed.

## Release Workflow (`release.yml`)

### Trigger Events
- Manual trigger via workflow_dispatch

### What it does
1. **Test Phase**:
   - Runs all unit tests
   - Fails the release if tests fail

2. **Build and Release Phase** (only if tests pass):
   - Calculates the next version using calendar versioning (YYYY.MM.PATCH)
   - Updates version in `chatrixcd/__init__.py` and `setup.py`
   - Updates `CHANGELOG.md`:
     - Moves content from "Unreleased" section to a new version section
     - Adds the release version and date to the new section
     - Clears the "Unreleased" section for future changes
     - Updates the "Version History" section with the new release
   - Generates changelog from git commits since last release
   - Commits version changes (including CHANGELOG.md)
   - Creates and pushes a git tag
   - Creates a GitHub release with the generated changelog

### Version Format
- **Calendar Versioning (CalVer)**: YYYY.MM.PATCH
- Example: `2024.12.0`, `2024.12.1`, `2025.01.0`

### Version Types
All version types increment the PATCH number in the YYYY.MM.PATCH format. The type selection indicates the nature of changes:

- **patch**: Bug fixes and minor improvements (e.g., 2024.12.0 → 2024.12.1)
- **minor**: New features and enhancements (e.g., 2024.12.1 → 2024.12.2)
- **major**: Breaking changes or major milestones (e.g., 2024.12.2 → 2024.12.3)

The patch number automatically resets to 0 when the month changes (e.g., 2024.12.5 → 2025.01.0).

### How to use
1. Go to **Actions** tab in GitHub
2. Select **Build and Release** workflow
3. Click **Run workflow**
4. Select **version_type** (patch or minor)
5. Click **Run workflow**

### Prerequisites
- All unit tests must pass
- The workflow needs write permissions for contents (already configured)

## Version Calculation Logic

The release workflow automatically determines the next version:

1. Gets the current year and month (e.g., 2024-12)
2. Finds the latest tag for this month (e.g., `2024.12.2`)
3. Increments the patch number (e.g., `2024.12.3`)
4. If no tag exists for the current month, starts with patch 0 or 1 (depending on version type)

## Changelog Management

The release workflow manages changelogs in two ways:

### 1. CHANGELOG.md Update
- **Automatic Processing**: The workflow automatically updates `CHANGELOG.md` during release
- **Content Migration**: Moves all content from the `[Unreleased]` section to a new version section
- **Version Section**: Creates a new section with format `## [VERSION] - YYYY-MM-DD`
- **Unreleased Reset**: Clears the `[Unreleased]` section after moving content
- **Version History**: Updates the "Version History" section with the new release

### 2. GitHub Release Changelog
- **Generated from Git**: Automatically generated from git commit messages
- **Includes**: All commits since the last release
- **Format**: `- <commit message> (<short hash>)`
- **Comparison Link**: Includes a link to the full changelog on GitHub

### Maintaining CHANGELOG.md

To ensure proper changelog updates:
1. **Add changes under `[Unreleased]`**: Document all changes in the Unreleased section as you develop
2. **Use standard format**: Follow [Keep a Changelog](https://keepachangelog.com/) format
3. **Organize by type**: Use sections like "Added", "Changed", "Fixed", "Removed"
4. **Be descriptive**: Write clear descriptions of changes
5. **Before release**: Review the Unreleased section to ensure completeness

Example structure:
```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Changed behavior description

### Fixed
- Bug fix description
```

When you run the release workflow, this content will automatically move to a versioned section.

## Best Practices

1. **Commit Messages**: Write clear, descriptive commit messages as they will appear in the changelog
2. **Testing**: Always ensure tests pass locally before creating a release
3. **Version Type**: Choose the appropriate version type to indicate the nature of changes:
   - Use "patch" for bug fixes and minor improvements
   - Use "minor" for new features and enhancements
   - Use "major" for breaking changes or major milestones
4. **Frequency**: Create releases regularly to keep the changelog manageable
