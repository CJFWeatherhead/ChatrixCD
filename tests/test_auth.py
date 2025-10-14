"""Tests for authentication module."""

import unittest
from chatrixcd.auth import MatrixAuth


class TestMatrixAuth(unittest.TestCase):
    """Test Matrix authentication handler."""

    def test_init_password_auth(self):
        """Test initialization with password authentication."""
        config = {
            'auth_type': 'password',
            'user_id': '@bot:example.com',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.auth_type, 'password')

    def test_init_oidc_auth(self):
        """Test initialization with OIDC authentication."""
        config = {
            'auth_type': 'oidc',
            'oidc_redirect_url': 'http://localhost:8080/callback'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.auth_type, 'oidc')

    def test_get_auth_type(self):
        """Test getting authentication type."""
        config = {
            'auth_type': 'password',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.get_auth_type(), 'password')

    def test_get_password(self):
        """Test getting password from config."""
        config = {
            'auth_type': 'password',
            'password': 'testpass123'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.get_password(), 'testpass123')

    def test_get_password_missing(self):
        """Test getting password when not configured."""
        config = {
            'auth_type': 'password'
        }
        auth = MatrixAuth(config)
        
        self.assertIsNone(auth.get_password())

    def test_get_oidc_redirect_url(self):
        """Test getting OIDC redirect URL from config."""
        config = {
            'auth_type': 'oidc',
            'oidc_redirect_url': 'http://localhost:8080/callback'
        }
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.get_oidc_redirect_url(), 'http://localhost:8080/callback')

    def test_get_oidc_redirect_url_default(self):
        """Test getting OIDC redirect URL with default value when not configured."""
        config = {
            'auth_type': 'oidc'
        }
        auth = MatrixAuth(config)
        
        # Should return default value, not None
        self.assertEqual(auth.get_oidc_redirect_url(), 'http://localhost:8080/callback')

    def test_validate_config_password_valid(self):
        """Test validation of valid password configuration."""
        config = {
            'auth_type': 'password',
            'password': 'testpass'
        }
        auth = MatrixAuth(config)
        
        is_valid, error_msg = auth.validate_config()
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_config_password_missing(self):
        """Test validation of password configuration without password."""
        config = {
            'auth_type': 'password'
        }
        auth = MatrixAuth(config)
        
        is_valid, error_msg = auth.validate_config()
        self.assertFalse(is_valid)
        self.assertIn('password', error_msg.lower())

    def test_validate_config_oidc_valid(self):
        """Test validation of valid OIDC configuration."""
        config = {
            'auth_type': 'oidc',
            'oidc_redirect_url': 'http://localhost:8080/callback'
        }
        auth = MatrixAuth(config)
        
        is_valid, error_msg = auth.validate_config()
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_config_oidc_without_redirect_url(self):
        """Test validation of OIDC configuration without explicit redirect URL.
        
        OIDC redirect URL is now optional with a default value, so validation
        should pass even without explicit configuration.
        """
        config = {
            'auth_type': 'oidc'
        }
        auth = MatrixAuth(config)
        
        is_valid, error_msg = auth.validate_config()
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_config_unknown_auth_type(self):
        """Test validation with unknown authentication type."""
        config = {
            'auth_type': 'unknown'
        }
        auth = MatrixAuth(config)
        
        is_valid, error_msg = auth.validate_config()
        self.assertFalse(is_valid)
        self.assertIn('unknown', error_msg.lower())

    def test_default_auth_type(self):
        """Test that password is the default authentication type."""
        config = {}
        auth = MatrixAuth(config)
        
        self.assertEqual(auth.get_auth_type(), 'password')


if __name__ == '__main__':
    unittest.main()
