"""ChatrixCD - Matrix bot for CI/CD automation with Semaphore UI."""

import os
import subprocess

__version__ = "2025.12.17.6.1.2"


def _get_version_with_commit():
    """Get version with git commit if running from git repository.

    Returns:
        Version string with commit ID appended if running from git,
        otherwise just the version string.
    """
    try:
        # Check if we're in a git repository
        git_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".git")
        if os.path.exists(git_dir):
            # Get the short commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=1,
                cwd=os.path.dirname(os.path.dirname(__file__)),
            )
            if result.returncode == 0:
                commit_id = result.stdout.strip()
                return f"{__version__}-c{commit_id}"
    except Exception:
        # If anything fails, just return the base version
        pass

    return __version__


# Get the full version (with commit if available)
__version_full__ = _get_version_with_commit()
