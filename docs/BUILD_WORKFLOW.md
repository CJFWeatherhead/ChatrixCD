# Build Workflow Documentation

This document describes the build and release process for ChatrixCD, including how we create portable, statically-compiled binaries.

## Overview

ChatrixCD uses GitHub Actions to automatically build and release binaries for multiple Linux architectures. The build process creates statically-compiled binaries using Alpine Linux (musl libc) to ensure maximum portability across different Linux distributions.

## Build Architecture

### Why Alpine Linux and musl?

We build all binaries on Alpine Linux using musl libc instead of glibc for several key reasons:

1. **Static Compilation**: musl is designed to support static linking, making it easier to create truly portable binaries
2. **Smaller Binaries**: musl produces smaller binaries compared to glibc
3. **No External Dependencies**: Static binaries include all required libraries (OpenSSL, libffi, etc.)
4. **Maximum Portability**: Binaries work across different Linux distributions without compatibility issues
5. **No glibc Version Conflicts**: Eliminates the common problem of glibc version mismatches between systems

### Supported Architectures

- **x86_64** (64-bit Intel/AMD): Built using Alpine 3.22
- **i686** (32-bit Intel/AMD): Built using Alpine 3.22
- **arm64** (64-bit ARM): Built using Alpine 3.22

All architectures are now built using the same `Dockerfile.build` with platform-specific configurations.

## Build Process

### 1. Test Phase

Before building, the workflow runs all unit tests to ensure code quality:

```yaml
- name: Run unit tests
  run: |
    python -m unittest discover -s tests -v
```

### 2. Build Phase

Each architecture is built in parallel using Docker containers with Alpine Linux:

#### Build Dependencies

All builds require these Alpine packages:
- `gcc`, `g++`: C/C++ compilers
- `musl-dev`: musl development headers
- `patchelf`: ELF binary patcher
- `ccache`: Compiler cache for faster builds
- `linux-headers`: Linux kernel headers
- `libffi-dev`: Foreign Function Interface library
- `openssl-dev`: OpenSSL cryptographic library
- `rust`, `cargo`: Rust toolchain (for some Python dependencies)
- `git`, `make`: Version control and build tools

#### Nuitka Configuration

We use Nuitka to compile Python code to C and create standalone binaries with these key options:

- `--mode=onefile`: Create a single executable file
- `--output-filename=chatrixcd-linux-{arch}`: Name the output binary
- `--enable-plugin=anti-bloat`: Reduce binary size by removing unnecessary imports
- `--assume-yes-for-downloads`: Automatically download required tools
- `--static-libpython=yes`: **Statically link the Python interpreter** (no external libpython required)
- `--lto=yes/no`: **Link-time optimization** (enabled for x86_64/i686, disabled for ARM64 for faster builds)
- `--jobs=4`: **Parallel compilation** using 4 CPU cores
- `--linux-icon=assets/icon.png`: Embed application icon
- `--include-data-dir=assets=assets`: Include asset files in the binary

#### Build Method: Docker Buildx with BuildKit

We use **Docker buildx** with BuildKit for all architecture builds. This provides:
- Better layer caching with BuildKit cache mounts
- GitHub Actions cache integration
- Optimized multi-platform builds
- Cleaner and more maintainable build process

The build process is defined in `Dockerfile.build`:
```dockerfile
FROM alpine:3.22 AS builder
RUN apk add --no-cache python3 py3-pip build-base python3-dev gcc g++ musl-dev \
    patchelf ccache linux-headers libffi-dev openssl-dev rust cargo git make
ENV CCACHE_DIR=/root/.ccache PATH=/usr/lib/ccache/bin:$PATH
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH" VIRTUAL_ENV="/venv"
WORKDIR /src
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install nuitka ordered-set
COPY . .
ARG ARCH ENABLE_LTO=yes
RUN --mount=type=cache,target=/root/.ccache \
    python3 -m nuitka --mode=onefile \
    --output-filename=chatrixcd-linux-${ARCH} \
    --enable-plugin=anti-bloat \
    --assume-yes-for-downloads \
    --static-libpython=yes \
    --lto=${ENABLE_LTO} \
    --jobs=4 \
    --linux-icon=assets/icon.png \
    --include-data-dir=assets=assets \
    chatrixcd/main.py
FROM scratch AS export
ARG ARCH
COPY --from=builder /src/chatrixcd-linux-${ARCH} /
```

And invoked via GitHub Actions workflow:
```yaml
- name: Build with Nuitka using Docker Buildx
  uses: docker/build-push-action@v5
  with:
    context: .
    file: ./Dockerfile.build
    platforms: linux/amd64  # or linux/386, linux/arm64
    target: export
    build-args: |
      ARCH=x86_64
      ENABLE_LTO=yes
    cache-from: type=gha,scope=build-x86_64
    cache-to: type=gha,mode=max,scope=build-x86_64
    outputs: type=local,dest=.
```

**Key advantages over docker run**:
- BuildKit caches pip packages and ccache artifacts using `RUN --mount=type=cache`
- GitHub Actions cache persists BuildKit layers across workflow runs
- Better parallelization and optimization
- Cleaner separation of build logic (Dockerfile) from workflow
- Same Dockerfile works for all architectures with different platforms

### 3. Release Phase

After successful builds, the workflow:

1. **Calculates Version**: Uses semantic calendar versioning (YYYY.MM.DD.MAJOR.MINOR.PATCH)
2. **Updates Files**: Updates version in `chatrixcd/__init__.py` and `setup.py`
3. **Updates CHANGELOG**: Moves unreleased changes to the new version section
4. **Creates Git Tag**: Tags the release in the repository
5. **Creates GitHub Release**: Uploads all binaries and release notes

## Binary Characteristics

### What's Included

The statically-compiled binaries include:

- Python 3.12 interpreter (statically linked)
- All Python dependencies:
  - matrix-nio (Matrix client with E2E encryption)
  - aiohttp (async HTTP client)
  - hjson (human-friendly JSON parser)
  - colorlog (colored logging)
  - textual (TUI framework)
  - qrcode (QR code generation)
  - psutil (system utilities)
- All native libraries:
  - OpenSSL (cryptography)
  - libffi (foreign function interface)
  - Other system libraries
- Application assets (icons, etc.)

### What's NOT Required

Users do **not** need to install:

- Python interpreter
- Python packages
- System libraries (glibc, OpenSSL, etc.)
- Development tools

The binary is completely self-contained and portable.

## Portability Testing

Our binaries are designed to work on:

- ✅ Debian/Ubuntu and derivatives
- ✅ RHEL/CentOS/Fedora and derivatives
- ✅ Alpine Linux
- ✅ Arch Linux
- ✅ Other Linux distributions (any kernel 3.2+)

The binaries have been tested to ensure they work across different distributions without requiring any system dependencies.

## Manual Build

If you want to build the binary locally:

### Prerequisites

- Docker installed and running
- Source code checked out

### Build Commands

**For x86_64:**
```bash
docker run --rm -v "$PWD":/src -w /src python:3.12-alpine sh -c "
  apk add --no-cache gcc g++ musl-dev patchelf ccache linux-headers \
    libffi-dev openssl-dev rust cargo git make &&
  pip install --upgrade pip &&
  pip install -r requirements.txt &&
  pip install nuitka ordered-set &&
  python -m nuitka --mode=onefile \
    --output-filename=chatrixcd-linux-x86_64 \
    --enable-plugin=anti-bloat \
    --assume-yes-for-downloads \
    --static-libpython=yes \
    --lto=yes \
    --linux-icon=assets/icon.png \
    --include-data-dir=assets=assets \
    chatrixcd/main.py
"
```

**For arm64:**
```bash
docker run --rm --platform linux/arm64 -v "$PWD":/src -w /src arm64v8/alpine:3.22 sh -c "
  apk add --no-cache python3 py3-pip gcc g++ musl-dev patchelf ccache linux-headers \
    libffi-dev openssl-dev rust cargo git make &&
  pip3 install --break-system-packages --upgrade pip &&
  pip3 install --break-system-packages -r requirements.txt &&
  pip3 install --break-system-packages nuitka ordered-set &&
  python3 -m nuitka --mode=onefile \
    --output-filename=chatrixcd-linux-arm64 \
    --enable-plugin=anti-bloat \
    --assume-yes-for-downloads \
    --static-libpython=yes \
    --lto=yes \
    --linux-icon=assets/icon.png \
    --include-data-dir=assets=assets \
    chatrixcd/main.py
"
```

The binary will be created in the current directory.

## Verifying Static Compilation

To verify that a binary is statically linked, you can use the following commands:

### Check for Dynamic Dependencies

```bash
# Should show "not a dynamic executable" for static binaries
ldd chatrixcd-linux-x86_64

# Expected output for static binary:
#   not a dynamic executable
```

### Check for musl libc

```bash
# Should find "musl" in the binary strings
strings chatrixcd-linux-x86_64 | grep musl

# Expected output:
#   musl libc (...)
```

### Check File Type

```bash
file chatrixcd-linux-x86_64

# Expected output should mention:
#   ELF 64-bit LSB executable, statically linked
```

### Verification Script

You can also use this comprehensive verification script:

```bash
#!/bin/bash
BINARY="chatrixcd-linux-x86_64"

echo "Verifying static compilation of $BINARY"
echo "========================================"
echo ""

# Check file type
echo "1. File type:"
file "$BINARY"
echo ""

# Check for dynamic dependencies
echo "2. Dynamic dependencies:"
ldd "$BINARY" 2>&1 || echo "✅ Binary is statically linked"
echo ""

# Check for musl
echo "3. C library:"
if strings "$BINARY" | grep -q "musl"; then
    echo "✅ Built with musl libc"
else
    echo "⚠️  Not built with musl"
fi
echo ""

# Size
echo "4. Binary size:"
du -h "$BINARY"
echo ""

echo "✅ Verification complete"
```

## Troubleshooting

### Build Fails with Missing Dependencies

Ensure all build dependencies are installed in the Alpine container. The full list is:
```
gcc g++ musl-dev patchelf ccache linux-headers libffi-dev openssl-dev rust cargo git make
```

### Binary Doesn't Run on Target System

1. Check kernel version: `uname -r` (requires Linux 3.2+)
2. Ensure execute permissions: `chmod +x chatrixcd-linux-*`
3. Check architecture: `uname -m` must match binary architecture
4. Try running with `--version` flag to test basic functionality
5. Verify static compilation using commands above

### Binary Size Concerns

The static binaries are larger than dynamically-linked versions because they include:
- Python interpreter (~15-20 MB)
- All Python libraries (~20-30 MB)
- Native libraries (OpenSSL, etc.) (~5-10 MB)

This trade-off is intentional to provide maximum portability and eliminate all external dependencies.

## Version Management

Versions use Semantic Calendar Versioning: `YYYY.MM.DD.MAJOR.MINOR.PATCH`

- `YYYY.MM.DD`: Release date
- `MAJOR`: Breaking changes or major features (increments on major changes)
- `MINOR`: New features, non-breaking (increments on feature additions)
- `PATCH`: Bug fixes and security updates (increments on fixes)

The workflow supports three version types:
- `patch`: Increments the patch number
- `minor`: Increments the minor number, resets patch to 0
- `major`: Increments the major number, resets minor and patch to 0

## CI/CD Integration

The build workflow is triggered manually via workflow_dispatch:

```yaml
on:
  workflow_dispatch:
    inputs:
      version_type:
        description: 'Version type (minor or patch)'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major
```

To trigger a build:
1. Go to Actions → Build and Release
2. Click "Run workflow"
3. Select version type (patch/minor/major)
4. Click "Run workflow"

The workflow will:
1. Run tests
2. Build binaries for all architectures
3. Create a new release with version-tagged binaries

## Security Considerations

### Static Linking and Security Updates

While static linking provides portability, it means security updates to system libraries (like OpenSSL) require rebuilding the entire binary. We recommend:

1. Subscribe to security advisories for dependencies
2. Rebuild binaries promptly when security updates are released
3. Monitor GitHub Security Advisories for this repository

### Dependency Management

All dependencies are explicitly listed in `requirements.txt` with minimum version requirements:

```
matrix-nio[e2e]>=0.24.0
aiohttp>=3.9.0
hjson>=3.1.0
colorlog>=6.7.0
textual>=0.47.0
qrcode>=7.4.2
psutil>=5.9.0
PyYAML>=6.0
```

## Future Improvements

Potential enhancements to the build process:

1. **Binary Signing**: Add GPG signing for binary verification
2. **Checksums**: Generate and publish SHA256 checksums for all binaries
3. **Automated Testing**: Run binary tests on different distributions
4. **Size Optimization**: Further reduce binary size with advanced Nuitka options
5. **Reproducible Builds**: Ensure builds are bit-for-bit reproducible

## References

- [Nuitka Documentation](https://nuitka.net/)
- [Alpine Linux](https://alpinelinux.org/)
- [musl libc](https://musl.libc.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Calendar Versioning](https://calver.org/)
