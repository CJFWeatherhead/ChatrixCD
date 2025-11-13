"""Integration tests for live ChatrixCD instance.

This module tests ChatrixCD by connecting to a real Matrix server
and interacting with a running ChatrixCD bot instance.
"""

import os
import sys
import asyncio
import unittest
import json
from pathlib import Path
from typing import Optional
from nio import AsyncClient, RoomMessageText
from nio.responses import LoginResponse


class ChatrixCDIntegrationTest(unittest.IsolatedAsyncioTestCase):
    """Integration tests for ChatrixCD bot interactions."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        config_path = os.getenv('INTEGRATION_CONFIG')
        if not config_path:
            raise RuntimeError("INTEGRATION_CONFIG environment variable not set")

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Integration config not found: {config_file}")

        with open(config_file, 'r') as f:
            cls.config = json.load(f)

        cls.matrix_config = cls.config['matrix']
        cls.test_timeout = cls.config.get('test_timeout', 60)

    async def asyncSetUp(self):
        """Set up test client for each test."""
        self.client = AsyncClient(
            self.matrix_config['homeserver'],
            self.matrix_config['user_id']
        )

        # Login
        response = await self.client.login(
            password=self.matrix_config['password']
        )

        if not isinstance(response, LoginResponse):
            raise RuntimeError(f"Login failed: {response}")

        # Join the test room if not already joined
        await self.client.join(self.matrix_config['room_id'])

        # Set up event callback
        self.received_messages = []
        self.client.add_event_callback(
            self._on_room_message,
            RoomMessageText
        )

    async def asyncTearDown(self):
        """Clean up after each test."""
        await self.client.close()

    def _on_room_message(self, room, event):
        """Callback for room messages."""
        if room.room_id == self.matrix_config['room_id']:
            self.received_messages.append(event)

    async def _send_command_and_wait(self, command: str, timeout: int = 10) -> Optional[str]:
        """Send a command to the bot and wait for a response."""
        # Clear previous messages
        self.received_messages.clear()

        # Send the command
        await self.client.room_send(
            room_id=self.matrix_config['room_id'],
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": command
            }
        )

        # Wait for response from bot
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.5)

            # Check for messages from the bot
            for event in self.received_messages:
                if event.sender == self.matrix_config['bot_user_id']:
                    return event.body

        return None

    async def test_bot_responds_to_help(self):
        """Test that the bot responds to the help command."""
        response = await self._send_command_and_wait("!cd help")

        self.assertIsNotNone(response, "Bot did not respond to help command")
        self.assertIn("help", response.lower(), f"Help response should contain 'help': {response}")

    async def test_bot_responds_to_invalid_command(self):
        """Test that the bot responds to invalid commands."""
        response = await self._send_command_and_wait("!cd nonexistentcommand")

        self.assertIsNotNone(response, "Bot did not respond to invalid command")
        # Bot should respond with an error or help message

    async def test_bot_responds_to_pet_command(self):
        """Test the hidden pet command."""
        response = await self._send_command_and_wait("!cd pet")

        self.assertIsNotNone(response, "Bot did not respond to pet command")
        # Should be positive response

    async def test_bot_responds_to_scold_command(self):
        """Test the hidden scold command."""
        response = await self._send_command_and_wait("!cd scold")

        self.assertIsNotNone(response, "Bot did not respond to scold command")
        # Should be apologetic response

    async def test_bot_status_command(self):
        """Test the status command if available."""
        # This might require a running task, so we'll just check it doesn't crash
        response = await self._send_command_and_wait("!cd status nonexistent")

        self.assertIsNotNone(response, "Bot did not respond to status command")
        # Should indicate task not found or similar

    async def test_bot_projects_command(self):
        """Test the projects command."""
        response = await self._send_command_and_wait("!cd projects")

        self.assertIsNotNone(response, "Bot did not respond to projects command")
        # Should list projects or indicate connection issues


if __name__ == "__main__":
    # Load config for manual testing
    config_path = os.getenv('INTEGRATION_CONFIG', 'tests/integration_config.json')
    if not Path(config_path).exists():
        print(f"Config file not found: {config_path}")
        print("Please copy integration_config.json.example to integration_config.json and configure it.")
        sys.exit(1)

    unittest.main()