"""Authentication module with native Matrix SDK authentication support.

This module was developed with assistance from AI/LLM tools. It provides a simple
wrapper for Matrix authentication using password and OIDC/SSO methods.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MatrixAuth:
    """Handle Matrix authentication using native SDK methods.

    This class provides a simple wrapper for authentication configuration.
    Actual authentication is handled by matrix-nio's AsyncClient.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize authentication handler.

        Args:
            config: Matrix configuration dictionary
        """
        self.config = config
        self.auth_type = config.get("auth_type", "password")

    def get_auth_type(self) -> str:
        """Get the configured authentication type.

        Returns:
            Authentication type ('password' or 'oidc')
        """
        return self.auth_type

    def get_password(self) -> Optional[str]:
        """Get password for password authentication.

        Returns:
            Password string or None
        """
        return self.config.get("password")

    def get_oidc_redirect_url(self) -> str:
        """Get OIDC redirect URL from configuration.

        This is the URL where the user will be redirected after
        successful OIDC authentication. The URL should contain
        the loginToken parameter that will be provided to complete login.

        The redirect URL can be any URL - it doesn't need to be a running
        web server. The important part is the loginToken parameter that
        will be appended to the URL. Common patterns:
        - http://localhost:8080/callback (local development)
        - https://example.com/login-callback (production with web handler)
        - urn:ietf:wg:oauth:2.0:oob (out-of-band, for CLI apps)

        If not configured, defaults to http://localhost:8080/callback

        Returns:
            Redirect URL string (never None)
        """
        return self.config.get("oidc_redirect_url", "http://localhost:8080/callback")

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate authentication configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.auth_type == "password":
            password = self.get_password()
            if not password:
                return (
                    False,
                    "Password authentication requires 'password' in configuration",
                )
            return True, None

        elif self.auth_type == "oidc":
            # OIDC redirect URL is now optional with a sensible default
            return True, None

        else:
            return (
                False,
                f"Unknown auth_type: {self.auth_type}. Must be 'password' or 'oidc'",
            )
