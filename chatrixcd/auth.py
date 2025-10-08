"""Authentication module with OIDC support for Matrix."""

import logging
import base64
from typing import Optional, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)


class MatrixAuth:
    """Handle Matrix authentication including OIDC/token-based auth."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize authentication handler.
        
        Args:
            config: Matrix configuration dictionary
        """
        self.config = config
        self.auth_type = config.get('auth_type', 'password')
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    async def get_access_token(self) -> Optional[str]:
        """Get access token based on configured authentication type.
        
        Returns:
            Access token string or None if authentication fails
        """
        if self.auth_type == 'token':
            # Use pre-configured access token
            self.access_token = self.config.get('access_token')
            if self.access_token:
                logger.info("Using pre-configured access token")
                return self.access_token
            else:
                logger.error("Token auth configured but no access_token provided")
                return None
                
        elif self.auth_type == 'oidc':
            # Use OIDC flow to get token
            return await self._authenticate_oidc()
            
        elif self.auth_type == 'password':
            # Traditional password auth will be handled by matrix-nio
            logger.info("Using password authentication (handled by matrix-nio)")
            return None
            
        else:
            logger.error(f"Unknown auth_type: {self.auth_type}")
            return None

    async def _authenticate_oidc(self) -> Optional[str]:
        """Authenticate using OIDC flow with client credentials.
        
        Returns:
            Access token string or None if authentication fails
        """
        issuer = self.config.get('oidc_issuer')
        client_id = self.config.get('oidc_client_id')
        client_secret = self.config.get('oidc_client_secret')
        
        if not all([issuer, client_id, client_secret]):
            logger.error("OIDC authentication requires oidc_issuer, oidc_client_id, and oidc_client_secret")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # Discover OIDC endpoints
                discovery_url = f"{issuer}/.well-known/openid-configuration"
                async with session.get(discovery_url) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to discover OIDC endpoints: {resp.status}")
                        return None
                    discovery = await resp.json()
                    token_endpoint = discovery.get('token_endpoint')
                    
                if not token_endpoint:
                    logger.error("No token_endpoint found in OIDC discovery")
                    return None

                # Create basic auth header
                credentials = f"{client_id}:{client_secret}"
                b64_credentials = base64.b64encode(credentials.encode()).decode()
                
                # Request token using client credentials grant
                headers = {
                    'Authorization': f'Basic {b64_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'client_credentials',
                    'scope': 'openid'
                }
                
                async with session.post(token_endpoint, headers=headers, data=data) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Token request failed: {resp.status} - {error_text}")
                        return None
                        
                    token_response = await resp.json()
                    self.access_token = token_response.get('access_token')
                    self.refresh_token = token_response.get('refresh_token')
                    
                    if self.access_token:
                        logger.info("Successfully authenticated with OIDC")
                        return self.access_token
                    else:
                        logger.error("No access_token in OIDC response")
                        return None
            
        except Exception as e:
            logger.error(f"OIDC authentication failed: {e}")
            return None

    async def refresh_access_token(self) -> Optional[str]:
        """Refresh the access token if refresh token is available.
        
        Returns:
            New access token or None if refresh fails
        """
        if not self.refresh_token or self.auth_type != 'oidc':
            return None

        issuer = self.config.get('oidc_issuer')
        client_id = self.config.get('oidc_client_id')
        client_secret = self.config.get('oidc_client_secret')

        try:
            async with aiohttp.ClientSession() as session:
                # Discover token endpoint
                discovery_url = f"{issuer}/.well-known/openid-configuration"
                async with session.get(discovery_url) as resp:
                    discovery = await resp.json()
                    token_endpoint = discovery.get('token_endpoint')
                
                if not token_endpoint:
                    return None

                # Create basic auth header
                credentials = f"{client_id}:{client_secret}"
                b64_credentials = base64.b64encode(credentials.encode()).decode()
                
                # Request new token using refresh token
                headers = {
                    'Authorization': f'Basic {b64_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token
                }
                
                async with session.post(token_endpoint, headers=headers, data=data) as resp:
                    if resp.status != 200:
                        logger.error(f"Token refresh failed: {resp.status}")
                        return None
                        
                    token_response = await resp.json()
                    self.access_token = token_response.get('access_token')
                    self.refresh_token = token_response.get('refresh_token', self.refresh_token)
                    
                    logger.info("Successfully refreshed access token")
                    return self.access_token
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
