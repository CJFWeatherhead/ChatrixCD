"""Tests for authentication module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from chatrixcd.auth import MatrixAuth


class TestMatrixAuth(unittest.TestCase):
    """Test Matrix authentication handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_init_password_auth(self):
        """Test initialization with password authentication."""
        config = {
            'auth_type': 'password',
            'user_id': '@bot:example.com',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.auth_type, 'password')
        self.assertIsNone(auth.access_token)
        self.assertIsNone(auth.refresh_token)

    def test_init_token_auth(self):
        """Test initialization with token authentication."""
        config = {
            'auth_type': 'token',
            'user_id': '@bot:example.com',
            'access_token': 'test_token_123'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.auth_type, 'token')

    def test_init_oidc_auth(self):
        """Test initialization with OIDC authentication."""
        config = {
            'auth_type': 'oidc',
            'oidc_issuer': 'https://auth.example.com',
            'oidc_client_id': 'test_client',
            'oidc_client_secret': 'test_secret'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.auth_type, 'oidc')

    def test_get_access_token_password(self):
        """Test getting access token for password auth."""
        config = {
            'auth_type': 'password',
            'user_id': '@bot:example.com',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        # Password auth should return None (handled by matrix-nio)
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertIsNone(result)

    def test_get_access_token_token(self):
        """Test getting pre-configured access token."""
        config = {
            'auth_type': 'token',
            'access_token': 'test_token_abc'
        }
        auth = MatrixAuth(config)
        
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertEqual(result, 'test_token_abc')
        self.assertEqual(auth.access_token, 'test_token_abc')

    def test_get_access_token_token_missing(self):
        """Test token auth without access_token configured."""
        config = {
            'auth_type': 'token'
        }
        auth = MatrixAuth(config)
        
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertIsNone(result)

    def test_get_access_token_unknown_type(self):
        """Test with unknown authentication type."""
        config = {
            'auth_type': 'unknown'
        }
        auth = MatrixAuth(config)
        
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertIsNone(result)



    def test_oidc_auth_missing_config(self):
        """Test OIDC authentication with missing configuration."""
        config = {
            'auth_type': 'oidc',
            'oidc_issuer': 'https://auth.example.com'
            # Missing client_id and client_secret
        }
        auth = MatrixAuth(config)
        
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertIsNone(result)



    def test_refresh_access_token_no_refresh_token(self):
        """Test token refresh without refresh token."""
        config = {
            'auth_type': 'oidc',
            'oidc_issuer': 'https://auth.example.com',
            'oidc_client_id': 'test_client',
            'oidc_client_secret': 'test_secret'
        }
        auth = MatrixAuth(config)
        
        result = self.loop.run_until_complete(auth.refresh_access_token())
        self.assertIsNone(result)

    def test_refresh_access_token_wrong_auth_type(self):
        """Test token refresh with non-OIDC auth type."""
        config = {
            'auth_type': 'password'
        }
        auth = MatrixAuth(config)
        auth.refresh_token = 'some_token'
        
        result = self.loop.run_until_complete(auth.refresh_access_token())
        self.assertIsNone(result)

    def test_token_storage(self):
        """Test that tokens are properly stored after retrieval."""
        config = {
            'auth_type': 'token',
            'access_token': 'stored_token_xyz'
        }
        auth = MatrixAuth(config)
        
        # Get token
        result = self.loop.run_until_complete(auth.get_access_token())
        
        # Verify token is stored in the instance
        self.assertEqual(result, 'stored_token_xyz')
        self.assertEqual(auth.access_token, 'stored_token_xyz')

    def test_password_auth_returns_none(self):
        """Test that password auth returns None (delegated to matrix-nio)."""
        config = {
            'auth_type': 'password',
            'user_id': '@bot:example.com',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        # Password auth should return None (handled by nio)
        result = self.loop.run_until_complete(auth.get_access_token())
        self.assertIsNone(result)
        # Should not store any token
        self.assertIsNone(auth.access_token)

    def test_auth_type_determines_flow(self):
        """Test that auth_type correctly determines the authentication flow."""
        # Test each auth type
        for auth_type in ['password', 'token', 'oidc', 'unknown']:
            config = {
                'auth_type': auth_type,
                'access_token': 'test_token' if auth_type == 'token' else None
            }
            auth = MatrixAuth(config)
            self.assertEqual(auth.auth_type, auth_type)


if __name__ == '__main__':
    unittest.main()
