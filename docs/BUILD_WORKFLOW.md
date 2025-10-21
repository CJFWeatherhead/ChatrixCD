# Build and Release Workflow

This document describes the automated build and release workflow for ChatrixCD using Nuitka to create standalone executables.

## Overview

The build workflow (`build.yml`) uses [Nuitka-Action](https://github.com/Nuitka/Nuitka-Action) to compile ChatrixCD into standalone executables for multiple platforms:

- **Linux**: x86_64, i686 (32-bit), ARM64
- **Windows**: x86_64, ARM64
- **macOS**: Universal binary (x86_64 + ARM64)

## Workflow Triggers

### Automatic Triggers (Pre-release)

The workflow automatically runs when:
- A pull request is **merged** into the `main` branch
- Creates pre-release artifacts with `-dev` suffix
- Example version: `2025.10.21.0.0.1-dev`

### Manual Triggers (Production Release)

The workflow can be manually triggered for production releases:
1. Go to Actions → Build and Release → Run workflow
2. Select version type: `patch`, `minor`, or `major`
3. Choose whether to mark as pre-release
4. Production releases do not have `-dev` suffix

## Version Scheme

ChatrixCD uses calendar versioning with semantic versioning:

```
YYYY.MM.DD.MAJOR.MINOR.PATCH[-dev]
```

- **YYYY.MM.DD**: Current date
- **MAJOR.MINOR.PATCH**: Semantic version components
- **-dev**: Optional suffix for pre-releases

Example versions:
- `2025.10.21.0.0.1` - Production release
- `2025.10.21.0.0.1-dev` - Pre-release from PR merge

## Build Process

### Linux Builds

- **x86_64**: Built natively using Nuitka-Action
- **i686**: Cross-compiled using Docker with i386/python:3.12-slim
- **ARM64**: Cross-compiled using Docker with arm64v8/python:3.12-slim

Linux builds include:
- Icon: `assets/icon.png`
- Bundled assets directory
- Standalone executable (statically linked)

### Windows Builds

- **x86_64**: Built natively using Nuitka-Action
- **ARM64**: Built using Nuitka-Action with ARM64 target

Windows builds include:
- Icon: `assets/icon.ico`
- File metadata (version, description, copyright)
- Company name: "ChatrixCD Contributors"
- Bundled assets directory
- Standalone .exe file

### macOS Builds

- **Universal**: Single executable for both x86_64 and ARM64

macOS builds include:
- Icon: `assets/icon.png`
- Application bundle: `ChatrixCD.app`
- Universal binary supporting both architectures
- Bundled assets directory

## Build Artifacts

All builds produce standalone executables with included assets:

```
chatrixcd-linux-x86_64
chatrixcd-linux-i686
chatrixcd-linux-arm64
chatrixcd-windows-x86_64.exe
chatrixcd-windows-arm64.exe
chatrixcd-macos-universal
ChatrixCD.app/ (macOS app bundle)
```

Artifacts are:
- Uploaded to GitHub Actions (90-day retention)
- Attached to GitHub Releases

## Release Process

### For PR Merges (Automated Pre-release)

1. Unit tests run for all Python versions (3.12, 3.13, 3.14)
2. Builds are created for all platforms
3. Version is calculated with `-dev` suffix
4. GitHub Release is created as **pre-release**
5. Artifacts are attached to the release

### For Manual Releases (Production)

1. Developer triggers workflow manually
2. Selects version type (patch/minor/major)
3. Unit tests run
4. Builds are created for all platforms
5. Version files are updated (`__init__.py`, `setup.py`)
6. `CHANGELOG.md` is updated
7. Git tag is created
8. GitHub Release is created
9. Artifacts are attached to the release

## Testing

The workflow includes comprehensive testing:

### Unit Tests

All unit tests must pass before building:
```bash
python -m unittest discover -s tests -v
```

### Workflow Tests

Workflow configuration is validated:
```bash
python -m unittest tests.test_workflow -v
```

Tests verify:
- Workflow file syntax (YAML)
- Required jobs and steps
- Platform matrix configuration
- Nuitka-Action usage
- Metadata and icons
- Pre-release handling

### PR Checks

On pull requests (before merge):
- Unit tests run on Python 3.12, 3.13, 3.14
- Workflow configuration tests run
- Actionlint validates workflow syntax

## Icons and Metadata

### Icons

- **icon.ico**: Windows executable icon (multi-resolution)
- **icon.png**: macOS/Linux icon (512x512 PNG)
- Source: `assets/logo-icon.svg` (converted to PNG/ICO)

### Metadata (Windows)

- **Company**: ChatrixCD Contributors
- **Product**: ChatrixCD
- **Description**: Matrix bot for CI/CD automation with Semaphore UI
- **Copyright**: Copyright (c) 2024 ChatrixCD Contributors
- **Version**: Matches release version

## Troubleshooting

### Build Failures

If a platform build fails:
1. Check the GitHub Actions logs for that specific job
2. Look for Nuitka compilation errors
3. Verify dependencies are correctly specified in `requirements.txt`
4. Ensure assets directory structure is correct

### Cross-compilation Issues

For i686 and ARM64 Linux builds:
- These use Docker for cross-compilation
- Requires QEMU emulation (automatically set up)
- May be slower than native builds
- Check Docker logs for compilation errors

### Version Conflicts

If version tagging fails:
- Check if the version already exists
- Verify CHANGELOG.md format
- Ensure git repository is clean

## Development

### Testing Workflow Locally

You cannot run GitHub Actions locally, but you can:

1. **Test workflow syntax**:
   ```bash
   actionlint .github/workflows/build.yml
   ```

2. **Test workflow configuration**:
   ```bash
   python -m unittest tests.test_workflow -v
   ```

3. **Test builds locally** (not recommended due to Nuitka complexity):
   ```bash
   pip install nuitka ordered-set
   python -m nuitka --onefile --standalone chatrixcd/main.py
   ```

### Modifying the Workflow

When modifying `build.yml`:
1. Update the workflow file
2. Run workflow tests to verify changes
3. Run actionlint to check syntax
4. Update this documentation if needed
5. Test on a PR to verify changes work

### Adding New Platforms

To add a new platform:
1. Add a new matrix entry in the appropriate job
2. Configure Nuitka-Action parameters for that platform
3. Update workflow tests to verify the new platform
4. Update this documentation

## Documentation Updates After Release

When a new production release is created, the documentation contains direct download links that automatically point to the latest release. **These links require no manual updates** as they use GitHub's `/releases/latest/download/` URL pattern.

### Download Link Format

All documentation uses the following URL pattern:

```
https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/<artifact-name>
```

Examples:
- `https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64`
- `https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-windows-x86_64.exe`
- `https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-macos-universal`

GitHub automatically redirects these URLs to the latest non-pre-release version.

### Files Containing Download Links

The following files contain download links that are automatically updated by GitHub's URL resolution:

1. **README.md** - Main repository documentation
2. **INSTALL.md** - Installation guide
3. **QUICKSTART.md** - Quick start guide
4. **docs/index.md** - Documentation homepage
5. **docs/installation.md** - Installation page (GitHub Pages)
6. **docs/quickstart.md** - Quick start page (GitHub Pages)

### Release Checklist

When creating a new production release:

- [ ] Trigger the build workflow manually (Actions → Build and Release)
- [ ] Select version type (major/minor/patch)
- [ ] Ensure "Mark as pre-release" is **unchecked**
- [ ] Wait for build to complete (~15-25 minutes)
- [ ] Verify all artifacts are attached to the release
- [ ] **No documentation updates needed** - links auto-update!
- [ ] Verify download links work by testing them
- [ ] Announce release in appropriate channels

### Testing Download Links

After a release, verify the download links work:

```bash
# Test Linux x86_64 link
curl -I https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64

# Should return HTTP 302 redirect to actual release URL
# Followed by HTTP 200 OK
```

### Pre-release Notes

Pre-releases (created automatically on PR merge):
- Are marked as "pre-release" on GitHub
- Have `-dev` suffix in version (e.g., `2025.10.21.0.0.1-dev`)
- Are **NOT** included in `/releases/latest/` URLs
- Are accessible via direct version URLs
- Are intended for testing only

### Manual Link Updates (If Needed)

In the rare case that artifact names change, update the following pattern in all documentation files:

**Old pattern:**
```
/releases/latest/download/chatrixcd-<platform>-<arch>
```

**Update in these files:**
- README.md
- INSTALL.md
- QUICKSTART.md
- docs/index.md
- docs/installation.md
- docs/quickstart.md

**Search and replace example:**
```bash
# If renaming linux-x86_64 to linux-amd64
find . -name "*.md" -exec sed -i 's/chatrixcd-linux-x86_64/chatrixcd-linux-amd64/g' {} \;
```

## Security Considerations

### Credentials

- GitHub Actions uses `GITHUB_TOKEN` for releases
- No additional secrets required
- Artifacts are publicly downloadable from releases

### Build Environment

- All builds run in isolated GitHub Actions runners
- No persistent state between builds
- Dependencies are installed fresh for each build

## Performance

Typical build times:
- Linux x86_64: ~5-10 minutes
- Linux i686 (Docker): ~10-15 minutes
- Linux ARM64 (Docker): ~10-15 minutes
- Windows x86_64: ~5-10 minutes
- Windows ARM64: ~5-10 minutes
- macOS Universal: ~10-15 minutes
- Total workflow time: ~15-25 minutes (parallel builds)

## References

- [Nuitka-Action Documentation](https://github.com/Nuitka/Nuitka-Action)
- [Nuitka Documentation](https://nuitka.net/doc/user-manual.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ChatrixCD Architecture](ARCHITECTURE.md)
