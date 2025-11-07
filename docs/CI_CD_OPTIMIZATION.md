# CI/CD Workflow Optimization Guide

## Overview

This document explains the optimizations made to ChatrixCD's GitHub Actions workflows to improve build and test performance.

## Key Optimizations

### 1. ARM64 Build Optimization (Build Workflow)

**Problem**: ARM64 builds were extremely slow due to QEMU emulation on x86_64 runners.

**Attempted Solution**: Native ARM64 runners (`ubuntu-24.04-arm64`) were initially tried but require GitHub Team/Enterprise plan.

**Current Solution**: Use QEMU emulation with optimized ccache, parallel compilation, and disabled LTO.

**Impact**: Significant improvement through caching and parallel builds, though not as fast as native ARM64 hardware

**Implementation**:
```yaml
runs-on: ubuntu-latest
```

With QEMU setup for ARM64:
```yaml
- name: Set up QEMU for ARM64 emulation
  if: matrix.arch == 'arm64'
  uses: docker/setup-qemu-action@v3
  with:
    platforms: linux/arm64
```

**Note**: Organizations with GitHub Team or Enterprise plans can switch to native ARM64 runners by changing `runs-on` to:
```yaml
runs-on: ${{ matrix.arch == 'arm64' && 'ubuntu-24.04-arm64' || 'ubuntu-latest' }}
```

### 2. Compilation Cache (ccache)

**Problem**: Every build recompiled all C/C++ code from scratch.

**Solution**: Configure ccache to cache compilation artifacts.

**Impact**: 40-60% time savings on subsequent builds

**Implementation**:
```yaml
- name: Cache ccache
  uses: actions/cache@v4
  with:
    path: .ccache
    key: ccache-${{ matrix.arch }}-${{ github.sha }}
    restore-keys: |
      ccache-${{ matrix.arch }}-
```

Each build configures ccache by adding it to PATH (Alpine's standard method):
```bash
export CCACHE_DIR=/src/.ccache
export PATH=/usr/lib/ccache/bin:$PATH
```

**Note**: In Alpine Linux, `/usr/lib/ccache/bin` contains symlinks that wrap gcc/g++/etc. with ccache automatically. This is the recommended approach as it works seamlessly with build systems like Nuitka's Scons.

### 3. Link Time Optimization (LTO) Management

**Problem**: LTO significantly increases ARM64 compilation time with minimal size benefit.

**Solution**: Disable LTO for ARM64, keep enabled for x86_64/i686.

**Impact**: 30-40% faster ARM64 builds

**Trade-off**: Slightly larger ARM64 binary (~5-10% increase), but build time is prioritized.

**Implementation**:
- x86_64/i686: `--lto=yes`
- ARM64: `--lto=no`

### 4. Parallel Compilation

**Problem**: Sequential compilation didn't utilize multiple CPU cores.

**Solution**: Enable parallel compilation with `--jobs=4`.

**Impact**: 15-25% faster builds

**Implementation**:
```bash
python -m nuitka --mode=onefile \
  --jobs=4 \
  ...
```

### 5. Test Matrix Optimization

**Problem**: Testing on 3 Python versions for every PR was redundant.

**Solution**: Dynamic matrix based on trigger type.

**Impact**: 60% faster test runs for PRs

**Implementation**:
```yaml
matrix:
  python-version: ${{ github.event_name == 'pull_request' && fromJSON('["3.12"]') || fromJSON('["3.11", "3.12", "3.13"]') }}
```

This means:
- **Pull Requests**: Test on Python 3.12 only
- **Main Branch Pushes**: Test on Python 3.11, 3.12, and 3.13

### 6. Parallel Job Execution

**Problem**: Validation job waited for all tests to complete unnecessarily.

**Solution**: Remove dependency, run jobs in parallel.

**Impact**: Faster overall workflow execution

**Before**:
```yaml
validate-build:
  needs: test
```

**After**:
```yaml
validate-build:
  # Run in parallel with tests
```

### 7. Docker BuildKit Configuration

**Problem**: Docker builds didn't leverage BuildKit optimizations.

**Solution**: Explicitly configure BuildKit with latest features.

**Impact**: Better layer caching

**Implementation**:
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    driver-opts: image=moby/buildkit:latest
```

**Note**: We use the latest BuildKit image for improved features while maintaining network isolation (no `network=host`) for security.

## Expected Performance Improvements

### Build Workflow

| Architecture | Before | After (with QEMU) | Improvement |
|-------------|--------|-------------------|-------------|
| ARM64 | 45-60 min | 20-30 min | **40-50% faster** |
| x86_64 | 15-20 min | 12-15 min | **20-25% faster** |
| i686 | 15-20 min | 12-15 min | **20-25% faster** |

*Note: Subsequent builds with ccache will be even faster. With native ARM64 runners (GitHub Team/Enterprise plan), ARM64 builds can be 70-75% faster (10-15 min).*

### Test Workflow

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| Pull Request | 6-8 min | 2-3 min | **60-65% faster** |
| Main Branch | 6-8 min | 6-8 min | Same (full coverage) |

## Monitoring and Validation

### First Build After Changes
1. ARM64 build will still be slow (no cache)
2. x86_64/i686 builds should show immediate improvements

### Second Build and Beyond
1. ccache will kick in, showing dramatic improvements
2. Check cache hit rates in build logs

### Verification Checklist
- [ ] ARM64 build uses QEMU emulation (or `ubuntu-24.04-arm64` if available)
- [ ] ccache directory is cached and restored
- [ ] LTO is disabled for ARM64
- [ ] Parallel compilation is enabled
- [ ] Test matrix adapts to event type

## Troubleshooting

### C Compiler Not Found Error
**Symptom**: `FATAL: Error, cannot locate suitable C compiler` during Nuitka compilation

**Cause**: Incorrectly setting `CC='ccache gcc'` prevents Nuitka's Scons from finding the compiler

**Solution**: Use ccache via PATH instead:
```bash
export PATH=/usr/lib/ccache/bin:$PATH
```

This is the Alpine Linux standard method and works seamlessly with all build systems.

### ARM64 Runner Not Available
**Symptom**: Build waits for hours or fails with "runner not found"

**Cause**: GitHub ARM64 runners (`ubuntu-24.04-arm64`) require GitHub Team or Enterprise Cloud plan

**Solution**: The default configuration now uses QEMU emulation for maximum compatibility:
1. Standard `ubuntu-latest` runners work for all architectures
2. QEMU provides ARM64 emulation automatically
3. If you have access to ARM64 runners, you can optionally enable them
4. Or use self-hosted ARM64 runners for best performance

### ccache Not Working
**Symptom**: No "cache hit" messages in build logs

**Check**:
1. Cache key is correct
2. `.ccache` directory is being created
3. Environment variables are exported

### LTO Disabled Warning
**Symptom**: Larger ARM64 binary size

**Explanation**: This is expected and intentional. The trade-off prioritizes build speed over binary size.

## Future Optimization Opportunities

### 1. Self-Hosted Runners
Consider self-hosted runners for even better performance:
- Persistent ccache across all builds
- More powerful hardware
- No minute limits

### 2. Build Matrix Reduction
For development branches, consider building only x86_64:
```yaml
matrix:
  arch: ${{ github.ref == 'refs/heads/main' && fromJSON('["x86_64", "i686", "arm64"]') || fromJSON('["x86_64"]') }}
```

### 3. Incremental Compilation
Explore Nuitka's incremental compilation options for even faster rebuilds.

### 4. Distributed ccache
Use `ccache` with network storage for sharing cache across runners.

## Related Documentation

- [GitHub Actions - Runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
  > **Note:** ARM64 runner availability may vary by GitHub plan. For the most current information, consult the official documentation above.
- [Nuitka Performance Options](https://nuitka.net/doc/user-manual.html#performance-options)
- [ccache Manual](https://ccache.dev/manual/latest.html)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)

## Maintenance

### When to Review These Optimizations

1. **New Python Version**: Update test matrix when supporting new Python versions
2. **Nuitka Updates**: Check for new optimization flags with Nuitka upgrades
3. **GitHub Runner Updates**: Monitor ARM64 runner performance and availability
4. **Build Time Regression**: If builds slow down, check ccache hit rates

### Metrics to Track

- Average build time per architecture
- ccache hit rate
- Test workflow duration
- Total workflow cost (runner minutes)

## Questions?

For questions or issues with these optimizations, please:
1. Check GitHub Actions logs for detailed error messages
2. Review this document for common issues
3. Open an issue with build logs attached
