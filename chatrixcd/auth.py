"""Authentication module with native Matrix SDK authentication support."""

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
        self.auth_type = config.get('auth_type', 'password')

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
        return self.config.get('password')

    def get_oidc_redirect_url(self) -> Optional[str]:
        """Get OIDC redirect URL from configuration.
        
        This is the URL where the user will be redirected after
        successful OIDC authentication. The URL should handle
        extracting the loginToken parameter.
        
        Returns:
            Redirect URL string or None
        """
        return self.config.get('oidc_redirect_url')

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate authentication configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.auth_type == 'password':
            password = self.get_password()
            if not password:
                return False, "Password authentication requires 'password' in configuration"
            return True, None
            
        elif self.auth_type == 'oidc':
            redirect_url = self.get_oidc_redirect_url()
            if not redirect_url:
                return False, "OIDC authentication requires 'oidc_redirect_url' in configuration"
            return True, None
            
        else:
            return False, f"Unknown auth_type: {self.auth_type}. Must be 'password' or 'oidc'"
