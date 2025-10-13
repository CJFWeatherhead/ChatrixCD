# GitHub Actions Workflows

This repository uses GitHub Actions for continuous integration and automated releases.

## Test Workflow (`test.yml`)

### Trigger Events
- Pull requests to `main` or `develop` branches
- Push to `main` branch

### What it does
1. Checks out the code
2. Sets up Python (versions 3.9, 3.10, 3.11, 3.12)
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
- **Semantic Calendar Versioning**: YYYY.MM.DD.MAJOR.MINOR.PATCH
- Example: `2025.10.12.1.0.1`, `2025.11.15.1.1.0`, `2025.12.01.2.0.0`
- Components:
  - `YYYY.MM.DD`: Release date (year, month, day)
  - `MAJOR`: Breaking changes or major features
  - `MINOR`: New features, non-breaking changes
  - `PATCH`: Bug fixes and security updates

**Historical Note**: Versions prior to October 2025 used `YYYY.MM.PATCH` format (e.g., `2025.10.8`).

### Version Types
Version numbers (MAJOR, MINOR, PATCH) always increment from the previous version and never reset:

- **major**: Breaking changes or major features (increments MAJOR, resets MINOR and PATCH to 0)
  - Example: `2025.10.12.1.5.3` → `2025.10.13.2.0.0`
- **minor**: New features, non-breaking changes (increments MINOR, resets PATCH to 0)
  - Example: `2025.10.12.1.5.3` → `2025.10.13.1.6.0`
- **patch**: Bug fixes and security updates (increments PATCH)
  - Example: `2025.10.12.1.5.3` → `2025.10.13.1.5.4`

### How to use
1. Go to **Actions** tab in GitHub
2. Select **Build and Release** workflow
3. Click **Run workflow**
4. Select **version_type** (major, minor, or patch)
5. Click **Run workflow**

### Prerequisites
- All unit tests must pass
- The workflow needs write permissions for contents (already configured)

## Version Calculation Logic

The release workflow automatically determines the next version:

1. Gets the current date (year, month, day)
2. Finds the latest tag with the new version format (YYYY.MM.DD.MAJOR.MINOR.PATCH)
3. Based on version type:
   - **major**: Increments MAJOR by 1, resets MINOR and PATCH to 0
   - **minor**: Keeps MAJOR, increments MINOR by 1, resets PATCH to 0
   - **patch**: Keeps MAJOR and MINOR, increments PATCH by 1
4. Combines date and version numbers to create the new version

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
   - Use "patch" for bug fixes and security updates
   - Use "minor" for new features and enhancements (non-breaking)
   - Use "major" for breaking changes or major feature releases
4. **Frequency**: Create releases regularly to keep the changelog manageable
5. **Version Numbers**: MAJOR, MINOR, and PATCH numbers always increment from the previous version and never reset, ensuring each version is unique and comparable
