"""Tests for Semaphore client module."""

import unittest
from unittest.mock import AsyncMock, patch
import asyncio
from chatrixcd.semaphore import SemaphoreClient


class TestSemaphoreClient(unittest.TestCase):
    """Test Semaphore API client."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = SemaphoreClient('https://semaphore.example.com', 'test_token')

    def tearDown(self):
        """Clean up after tests."""
        if self.client.session and not self.client.session.closed:
            self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.base_url, 'https://semaphore.example.com')
        self.assertEqual(self.client.api_token, 'test_token')
        self.assertIsNone(self.client.session)

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SemaphoreClient('https://semaphore.example.com/', 'token')
        self.assertEqual(client.base_url, 'https://semaphore.example.com')

    @patch('aiohttp.ClientSession')
    def test_ensure_session(self, mock_session_class):
        """Test session creation."""
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        self.loop.run_until_complete(self.client._ensure_session())
        
        mock_session_class.assert_called_once()
        self.assertEqual(self.client.session, mock_session)



    @patch('aiohttp.ClientSession')
    def test_close_session(self, mock_session_class):
        """Test session closure."""
        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session_class.return_value = mock_session
        
        self.client.session = mock_session
        self.loop.run_until_complete(self.client.close())
        
        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
