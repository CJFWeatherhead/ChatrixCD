"""OIDC/SSO Authentication Plugin for ChatrixCD.

This plugin provides OIDC (OpenID Connect) authentication support for Matrix login.
When enabled, users can authenticate using SSO providers instead of passwords.

Features:
- Interactive OIDC authentication flow
- Support for multiple identity providers
- Session persistence and restoration
- TUI screen for token input
- Automatic provider detection
"""

import logging
import aiohttp
from typing import Optional
from nio import LoginResponse, LoginInfoResponse

from chatrixcd.plugin_manager import Plugin


class OIDCAuthPlugin(Plugin):
    """Plugin that provides OIDC/SSO authentication support."""
    
    def __init__(self, bot, config: dict):
        """Initialize OIDC auth plugin.
        
        Args:
            bot: Bot instance
            config: Plugin configuration
        """
        super().__init__(bot, config)
        self.logger = logging.getLogger(__name__)
        self.name = "oidc_auth"
        self.description = "OIDC/SSO Authentication"
        
        # Store reference to bot for authentication
        self.bot_instance = bot
        
        # Token callback will be set by TUI or main
        self.token_callback = None
        
    async def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if initialization successful
        """
        self.logger.info("OIDC Authentication plugin initialized")
        
        # Register this plugin as the OIDC handler
        if hasattr(self.bot_instance, 'oidc_plugin'):
            self.logger.warning("Another OIDC plugin is already registered")
            return False
            
        self.bot_instance.oidc_plugin = self
        return True
        
    async def start(self) -> bool:
        """Start the plugin.
        
        Returns:
            True if started successfully
        """
        self.logger.info("OIDC Authentication plugin started")
        return True
        
    async def stop(self):
        """Stop the plugin."""
        self.logger.info("OIDC Authentication plugin stopped")
        
    async def cleanup(self):
        """Clean up plugin resources."""
        if hasattr(self.bot_instance, 'oidc_plugin') and self.bot_instance.oidc_plugin == self:
            delattr(self.bot_instance, 'oidc_plugin')
        self.logger.info("OIDC Authentication plugin cleaned up")
        
    def get_status(self) -> dict:
        """Get plugin status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "active": True,
            "description": "OIDC/SSO authentication enabled",
            "callback_registered": self.token_callback is not None
        }
    
    def set_token_callback(self, callback):
        """Set the token callback function.
        
        Args:
            callback: Async function that accepts (sso_url, redirect_url, identity_providers)
                     and returns login token
        """
        self.token_callback = callback
        self.logger.debug("Token callback registered")
        
    async def login_oidc(self, bot) -> bool:
        """Perform OIDC authentication using Matrix SSO flow.
        
        Args:
            bot: Bot instance to authenticate
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Step 1: Get available login flows from server
            self.logger.info("Querying server for available login flows...")
            login_info = await bot.client.login_info()
            
            if not isinstance(login_info, LoginInfoResponse):
                self.logger.error(f"Failed to get login info: {login_info}")
                return False
            
            # Check if SSO login is supported
            if 'm.login.sso' not in login_info.flows and 'm.login.token' not in login_info.flows:
                self.logger.error(
                    "Server does not support SSO/OIDC login. "
                    f"Available flows: {login_info.flows}"
                )
                return False
            
            self.logger.info("Server supports SSO login")
            
            # Step 2: Get identity providers and build redirect URL
            identity_providers = await self._get_identity_providers(bot)
            sso_redirect_url, redirect_url = await self._build_redirect_url(bot, identity_providers)
            
            # Step 3: Get login token from user
            login_token = await self._get_token_from_user(
                sso_redirect_url, redirect_url, identity_providers
            )
            
            if not login_token:
                return False
            
            # Step 4: Complete login with token
            self.logger.info("Attempting login with provided token...")
            response = await bot.client.login(
                token=login_token,
                device_name=bot.device_name
            )
            
            if isinstance(response, LoginResponse):
                self.logger.info(f"Successfully logged in as {bot.user_id} via OIDC")
                bot._save_session(response.access_token, response.device_id)
                await bot.setup_encryption()
                return True
            else:
                # Provide helpful error message
                error_msg = str(response)
                if "Invalid login token" in error_msg or "M_FORBIDDEN" in error_msg:
                    self.logger.error(
                        f"OIDC login failed: {response}\n"
                        "The login token is invalid or has expired. This can happen if:\n"
                        "  1. The token was copied incorrectly\n"
                        "  2. Too much time has passed since authentication\n"
                        "  3. The token was already used\n"
                        "Please try the OIDC login process again."
                    )
                else:
                    self.logger.error(f"OIDC login failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"OIDC login error: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
    
    async def _get_identity_providers(self, bot) -> list:
        """Get list of identity providers from the Matrix server.
        
        Args:
            bot: Bot instance
            
        Returns:
            List of identity provider dictionaries with 'id', 'name', 'icon', 'brand'
        """
        identity_providers = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{bot.homeserver}/_matrix/client/v3/login") as resp:
                    if resp.status == 200:
                        response_data = await resp.json()
                        flows = response_data.get('flows', [])
                        
                        for flow in flows:
                            if flow.get('type') == 'm.login.sso':
                                identity_providers = flow.get('identity_providers', [])
                                break
                        
                        self.logger.debug(f"Found {len(identity_providers)} identity providers")
                    else:
                        self.logger.warning(f"Failed to get login flows: HTTP {resp.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch identity providers: {e}")
        
        return identity_providers
    
    async def _build_redirect_url(self, bot, identity_providers: list) -> tuple:
        """Build SSO redirect URL based on available identity providers.
        
        Args:
            bot: Bot instance
            identity_providers: List of available identity providers
            
        Returns:
            Tuple of (sso_redirect_url, redirect_url)
        """
        redirect_url = bot.auth.get_oidc_redirect_url()
        
        if identity_providers and len(identity_providers) == 1:
            # Single provider - use specific provider URL
            provider_id = identity_providers[0].get('id')
            sso_redirect_url = (
                f"{bot.homeserver}/_matrix/client/v3/login/sso/redirect/{provider_id}"
                f"?redirectUrl={redirect_url}"
            )
            self.logger.info(f"Using identity provider: {identity_providers[0].get('name', provider_id)}")
        else:
            # Multiple or no providers - use generic SSO URL
            sso_redirect_url = (
                f"{bot.homeserver}/_matrix/client/v3/login/sso/redirect"
                f"?redirectUrl={redirect_url}"
            )
            
            if identity_providers and len(identity_providers) > 1:
                self.logger.info(f"Multiple identity providers available ({len(identity_providers)})")
        
        self.logger.debug(f"SSO redirect URL: {sso_redirect_url}")
        return sso_redirect_url, redirect_url
    
    async def _get_token_from_user(self, sso_redirect_url: str, redirect_url: str, 
                                   identity_providers: list) -> Optional[str]:
        """Get OIDC login token from user after browser authentication.
        
        Args:
            sso_redirect_url: URL for user to visit
            redirect_url: Redirect URL after authentication
            identity_providers: List of available providers
            
        Returns:
            Login token string, or None if failed
        """
        if self.token_callback:
            # Use registered callback (e.g., from TUI)
            try:
                login_token = await self.token_callback(sso_redirect_url, redirect_url, identity_providers)
                if not login_token:
                    self.logger.error("No login token provided by callback")
                    return None
                return login_token
            except Exception as e:
                self.logger.error(f"Token callback failed: {e}")
                return None
        else:
            # Default: Display instructions and wait for console input
            self.logger.info("=" * 70)
            self.logger.info("OIDC Authentication Required")
            self.logger.info("=" * 70)
            self.logger.info("")
            self.logger.info("Please complete the following steps:")
            self.logger.info("1. Open this URL in your browser:")
            self.logger.info(f"   {sso_redirect_url}")
            self.logger.info("")
            self.logger.info("2. Log in with your credentials")
            self.logger.info("")
            self.logger.info("3. After successful login, you'll be redirected to:")
            self.logger.info(f"   {redirect_url}?loginToken=...")
            self.logger.info("")
            self.logger.info("4. Copy the 'loginToken' value from the URL")
            self.logger.info("")
            
            if identity_providers and len(identity_providers) > 1:
                self.logger.info("Available Identity Providers:")
                for i, idp in enumerate(identity_providers, 1):
                    self.logger.info(f"   {i}. {idp.get('name', idp.get('id', 'Unknown'))}")
                self.logger.info("")
            
            self.logger.info("=" * 70)
            login_token = input("Enter loginToken: ").strip()
            
            if not login_token:
                self.logger.error("No login token provided")
                return None
                
            return login_token
    
    def register_tui_screens(self) -> list:
        """Register TUI screens for this plugin.
        
        Returns:
            List of screen registrations
        """
        try:
            from chatrixcd.tui.plugins.oidc_tui import OIDCAuthPluginTUI
            
            tui_extension = OIDCAuthPluginTUI(self)
            return tui_extension.get_screen_registrations()
            
        except ImportError:
            self.logger.debug("TUI not available, skipping screen registration")
            return []


def create_plugin(bot, config: dict):
    """Plugin factory function.
    
    Args:
        bot: Bot instance
        config: Plugin configuration
        
    Returns:
        OIDCAuthPlugin instance
    """
    return OIDCAuthPlugin(bot, config)
