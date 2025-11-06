"""Tests for Semaphore client module."""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from chatrixcd.semaphore import SemaphoreClient


class TestSemaphoreClient(unittest.TestCase):
    """Test Semaphore API client."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = SemaphoreClient('https://semaphore.example.test', 'test_token')

    def tearDown(self):
        """Clean up after tests."""
        if self.client.session and not self.client.session.closed:
            self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.base_url, 'https://semaphore.example.test')
        self.assertEqual(self.client.api_token, 'test_token')
        self.assertTrue(self.client.ssl_verify)
        self.assertIsNone(self.client.ssl_ca_cert)
        self.assertIsNone(self.client.ssl_client_cert)
        self.assertIsNone(self.client.ssl_client_key)
        self.assertIsNone(self.client.session)

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = SemaphoreClient('https://semaphore.example.test/', 'token')
        self.assertEqual(client.base_url, 'https://semaphore.example.test')

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

    def test_get_projects_success(self):
        """Test successful project retrieval."""
        # Mock the response
        async def mock_json():
            return [
                {'id': 1, 'name': 'Project 1'},
                {'id': 2, 'name': 'Project 2'}
            ]
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = mock_json
        
        # Mock the session with proper context manager and close
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        # Inject session and run
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_projects())
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Project 1')
        self.assertEqual(result[1]['name'], 'Project 2')

    def test_get_projects_failure(self):
        """Test project retrieval with API error."""
        mock_response = MagicMock()
        mock_response.status = 500
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_projects())
        
        self.assertEqual(result, [])

    def test_get_projects_exception(self):
        """Test project retrieval with exception."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Connection error")
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_projects())
        
        self.assertEqual(result, [])

    def test_get_project_templates_success(self):
        """Test successful template retrieval."""
        async def mock_json():
            return [
                {'id': 1, 'name': 'Template 1', 'description': 'Test template'},
                {'id': 2, 'name': 'Template 2'}
            ]
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_project_templates(1))
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Template 1')
        self.assertEqual(result[0]['description'], 'Test template')

    def test_get_project_templates_failure(self):
        """Test template retrieval with API error."""
        mock_response = MagicMock()
        mock_response.status = 404
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_project_templates(999))
        
        self.assertEqual(result, [])

    def test_start_task_success(self):
        """Test successful task start."""
        async def mock_json():
            return {
                'id': 123,
                'template_id': 1,
                'status': 'waiting'
            }
        
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.start_task(1, 1))
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['status'], 'waiting')

    def test_start_task_with_options(self):
        """Test task start with debug and dry_run options."""
        async def mock_json():
            return {'id': 124}
        
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(
            self.client.start_task(1, 1, debug=True, dry_run=True)
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 124)

    def test_start_task_failure(self):
        """Test task start failure."""
        async def mock_text():
            return "Bad request"
        
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = mock_text
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.start_task(1, 999))
        
        self.assertIsNone(result)

    def test_get_task_status_success(self):
        """Test successful task status retrieval."""
        async def mock_json():
            return {
                'id': 123,
                'status': 'running',
                'start': '2024-01-01T00:00:00Z'
            }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_task_status(1, 123))
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'running')

    def test_get_task_status_failure(self):
        """Test task status retrieval failure."""
        mock_response = MagicMock()
        mock_response.status = 404
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_task_status(1, 999))
        
        self.assertIsNone(result)

    def test_get_task_output_success(self):
        """Test successful task output retrieval with JSON array format."""
        async def mock_json():
            # Semaphore returns JSON array of log entries
            return [
                {"id": 0, "task_id": 123, "time": "2025-11-06T17:35:21.360703911Z", "output": ""},
                {"id": 1, "task_id": 123, "time": "2025-11-06T17:35:21.360797727Z", "output": "PLAY [Set global variables] ****************************************************"},
                {"id": 2, "task_id": 123, "time": "2025-11-06T17:35:21.366692799Z", "output": ""},
                {"id": 3, "task_id": 123, "time": "2025-11-06T17:35:21.366763205Z", "output": "TASK [Add sync service host to inventory] **************************************"},
                {"id": 4, "task_id": 123, "time": "2025-11-06T17:35:21.38092541Z", "output": "\u001b[0;33mchanged: [localhost]\u001b[0m"},
            ]
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_task_output(1, 123))
        
        # Verify the output field from each log entry is extracted and joined
        # Expected format: empty line, PLAY line, empty line, TASK line, colored changed line
        expected = (
            "\n"
            "PLAY [Set global variables] ****************************************************\n"
            "\n"
            "TASK [Add sync service host to inventory] **************************************\n"
            "\u001b[0;33mchanged: [localhost]\u001b[0m"
        )
        self.assertEqual(result, expected)

    def test_get_task_output_failure(self):
        """Test task output retrieval failure."""
        mock_response = MagicMock()
        mock_response.status = 404
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_task_output(1, 999))
        
        self.assertIsNone(result)

    def test_get_task_output_fallback_plain_text(self):
        """Test task output retrieval with non-array JSON (fallback to string)."""
        async def mock_json():
            # If API returns non-array response, treat as plain text
            return "Plain text output"
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = mock_json
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.get_task_output(1, 123))
        
        self.assertEqual(result, "Plain text output")

    def test_stop_task_success(self):
        """Test successful task stop."""
        mock_response = MagicMock()
        mock_response.status = 204
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.stop_task(1, 123))
        
        self.assertTrue(result)

    def test_stop_task_failure(self):
        """Test task stop failure."""
        mock_response = MagicMock()
        mock_response.status = 400
        
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.close = AsyncMock()
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.stop_task(1, 123))
        
        self.assertFalse(result)

    def test_stop_task_exception(self):
        """Test task stop with exception."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Network error")
        
        self.client.session = mock_session
        result = self.loop.run_until_complete(self.client.stop_task(1, 123))
        
        self.assertFalse(result)

    def test_ssl_verify_disabled(self):
        """Test client initialization with SSL verification disabled."""
        client = SemaphoreClient('https://semaphore.example.test', 'token', ssl_verify=False)
        self.assertFalse(client.ssl_verify)
        ssl_context = client._create_ssl_context()
        self.assertFalse(ssl_context)

    def test_ssl_custom_ca_cert(self):
        """Test client initialization with custom CA certificate."""
        client = SemaphoreClient(
            'https://semaphore.example.test',
            'token',
            ssl_ca_cert='/path/to/ca.crt'
        )
        self.assertEqual(client.ssl_ca_cert, '/path/to/ca.crt')

    def test_ssl_client_cert(self):
        """Test client initialization with client certificate."""
        client = SemaphoreClient(
            'https://semaphore.example.test',
            'token',
            ssl_client_cert='/path/to/cert.crt',
            ssl_client_key='/path/to/key.key'
        )
        self.assertEqual(client.ssl_client_cert, '/path/to/cert.crt')
        self.assertEqual(client.ssl_client_key, '/path/to/key.key')

    def test_create_ssl_context_default(self):
        """Test SSL context creation with default settings."""
        client = SemaphoreClient('https://semaphore.example.test', 'token')
        ssl_context = client._create_ssl_context()
        self.assertIsNone(ssl_context)

    def test_create_ssl_context_no_verify(self):
        """Test SSL context creation with verification disabled."""
        client = SemaphoreClient('https://semaphore.example.test', 'token', ssl_verify=False)
        ssl_context = client._create_ssl_context()
        self.assertFalse(ssl_context)


if __name__ == '__main__':
    unittest.main()
