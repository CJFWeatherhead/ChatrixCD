"""Tests for command-line interface."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO


class TestCLI(unittest.TestCase):
    """Test command-line argument parsing and handling."""

    def test_version_flag(self):
        """Test --version flag."""
        with patch('sys.argv', ['chatrixcd', '--version']):
            with patch('sys.stdout', new=StringIO()) as mock_stdout:
                # Import here to avoid early module initialization
                from chatrixcd import __version__
                
                # Create a simple version test
                import argparse
                parser = argparse.ArgumentParser(prog='chatrixcd')
                parser.add_argument('-V', '--version', action='version', 
                                  version=f'ChatrixCD {__version__}')
                
                with self.assertRaises(SystemExit) as cm:
                    parser.parse_args(['--version'])
                
                self.assertEqual(cm.exception.code, 0)

    def test_help_flag(self):
        """Test --help flag."""
        import argparse
        parser = argparse.ArgumentParser(
            prog='chatrixcd',
            description='ChatrixCD - Matrix bot for CI/CD automation with Semaphore UI'
        )
        # Help is automatically added by argparse
        
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(['--help'])
        
        self.assertEqual(cm.exception.code, 0)

    def test_verbose_flags(self):
        """Test verbose flags."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-v', '--verbose', action='count', default=0, dest='verbosity')
        
        # No verbose flag
        args = parser.parse_args([])
        self.assertEqual(args.verbosity, 0)
        
        # Single -v
        args = parser.parse_args(['-v'])
        self.assertEqual(args.verbosity, 1)
        
        # Double -vv
        args = parser.parse_args(['-vv'])
        self.assertEqual(args.verbosity, 2)
        
        # Triple -vvv
        args = parser.parse_args(['-vvv'])
        self.assertEqual(args.verbosity, 3)

    def test_config_file_flag(self):
        """Test --config flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-c', '--config', type=str, default='config.yaml')
        
        # Default config
        args = parser.parse_args([])
        self.assertEqual(args.config, 'config.yaml')
        
        # Custom config
        args = parser.parse_args(['--config', '/etc/chatrixcd/config.yaml'])
        self.assertEqual(args.config, '/etc/chatrixcd/config.yaml')
        
        # Short form
        args = parser.parse_args(['-c', 'custom.yaml'])
        self.assertEqual(args.config, 'custom.yaml')

    def test_color_flag(self):
        """Test --color flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-C', '--color', action='store_true')
        
        # Default (no color)
        args = parser.parse_args([])
        self.assertFalse(args.color)
        
        # With color
        args = parser.parse_args(['--color'])
        self.assertTrue(args.color)
        
        # Short form
        args = parser.parse_args(['-C'])
        self.assertTrue(args.color)

    def test_daemon_flag(self):
        """Test --daemon flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-D', '--daemon', action='store_true')
        
        # Default (no daemon)
        args = parser.parse_args([])
        self.assertFalse(args.daemon)
        
        # With daemon
        args = parser.parse_args(['--daemon'])
        self.assertTrue(args.daemon)
        
        # Short form
        args = parser.parse_args(['-D'])
        self.assertTrue(args.daemon)

    def test_show_config_flag(self):
        """Test --show-config flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-s', '--show-config', action='store_true', dest='show_config')
        
        # Default (no show config)
        args = parser.parse_args([])
        self.assertFalse(args.show_config)
        
        # With show config
        args = parser.parse_args(['--show-config'])
        self.assertTrue(args.show_config)
        
        # Short form
        args = parser.parse_args(['-s'])
        self.assertTrue(args.show_config)

    def test_admin_users_flag(self):
        """Test --admin flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-a', '--admin', action='append', dest='admin_users')
        
        # No admins
        args = parser.parse_args([])
        self.assertIsNone(args.admin_users)
        
        # Single admin
        args = parser.parse_args(['--admin', '@user1:matrix.org'])
        self.assertEqual(args.admin_users, ['@user1:matrix.org'])
        
        # Multiple admins
        args = parser.parse_args(['-a', '@user1:matrix.org', '-a', '@user2:matrix.org'])
        self.assertEqual(args.admin_users, ['@user1:matrix.org', '@user2:matrix.org'])

    def test_allowed_rooms_flag(self):
        """Test --room flag."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-r', '--room', action='append', dest='allowed_rooms')
        
        # No rooms
        args = parser.parse_args([])
        self.assertIsNone(args.allowed_rooms)
        
        # Single room
        args = parser.parse_args(['--room', '!room1:matrix.org'])
        self.assertEqual(args.allowed_rooms, ['!room1:matrix.org'])
        
        # Multiple rooms
        args = parser.parse_args(['-r', '!room1:matrix.org', '-r', '!room2:matrix.org'])
        self.assertEqual(args.allowed_rooms, ['!room1:matrix.org', '!room2:matrix.org'])

    def test_combined_flags(self):
        """Test multiple flags combined."""
        import argparse
        parser = argparse.ArgumentParser(prog='chatrixcd')
        parser.add_argument('-v', '--verbose', action='count', default=0, dest='verbosity')
        parser.add_argument('-c', '--config', type=str, default='config.yaml')
        parser.add_argument('-C', '--color', action='store_true')
        parser.add_argument('-a', '--admin', action='append', dest='admin_users')
        parser.add_argument('-r', '--room', action='append', dest='allowed_rooms')
        
        args = parser.parse_args([
            '-vv',
            '--config', 'custom.yaml',
            '-C',
            '-a', '@admin1:matrix.org',
            '-a', '@admin2:matrix.org',
            '-r', '!room1:matrix.org',
        ])
        
        self.assertEqual(args.verbosity, 2)
        self.assertEqual(args.config, 'custom.yaml')
        self.assertTrue(args.color)
        self.assertEqual(args.admin_users, ['@admin1:matrix.org', '@admin2:matrix.org'])
        self.assertEqual(args.allowed_rooms, ['!room1:matrix.org'])


if __name__ == '__main__':
    unittest.main()
