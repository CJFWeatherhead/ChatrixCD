import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from nio import MatrixRoom, RoomMessageText

from chatrixcd.commands import CommandHandler


class TestRunMappedSwitches(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Patch create_task to run inline
        self.create_task_patcher = patch("asyncio.create_task")
        self.mock_create_task = self.create_task_patcher.start()

        async def run_inline(coro, *args, **kwargs):
            return await coro

        self.mock_create_task.side_effect = run_inline

        # Mock bot
        self.mock_bot = MagicMock()
        self.mock_bot.send_message = AsyncMock(return_value="evt1")
        self.mock_bot.plugin_manager = MagicMock()
        self.mock_bot.plugin_manager.get_task_monitor.return_value = None
        # Configure aliases plugin to return identity mapping
        alias_plugin = MagicMock()
        alias_plugin.resolve_alias.side_effect = lambda cmd: cmd
        self.mock_bot.plugin_manager.get_plugin.return_value = alias_plugin

        # Mock semaphore
        self.mock_semaphore = MagicMock()
        self.mock_semaphore.get_project_templates = AsyncMock(
            return_value=[{"id": 5, "name": "Template 5", "description": "Runs Ansible"}]
        )

        # Config
        self.config = {"command_prefix": "!cd", "allowed_rooms": [], "admin_users": []}
        self.handler = CommandHandler(self.mock_bot, self.config, self.mock_semaphore)

    def tearDown(self):
        self.create_task_patcher.stop()
        self.loop.close()

    def test_positional_tags_are_captured_in_confirmation(self):
        # Call run with positional tags as 3rd arg
        self.loop.run_until_complete(
            self.handler.run_task("!room:id", "@user:example.com", ["4", "5", "update,molecule"])
        )
        key = "!room:id:@user:example.com"
        self.assertIn(key, self.handler.pending_confirmations)
        conf = self.handler.pending_confirmations[key]
        self.assertEqual(conf.get("tags"), "update,molecule")

    def test_flags_parsed_via_handle_message(self):
        # Use handle_message to exercise shlex parsing of quotes
        self.mock_semaphore.get_project_templates = AsyncMock(
            return_value=[{"id": 1, "name": "Template 1"}]
        )
        room = MagicMock(spec=MatrixRoom)
        room.room_id = "!room:id"
        event = MagicMock(spec=RoomMessageText)
        event.sender = "@user:example.com"
        event.event_id = "evt-xyz"
        event.body = '!cd run 3 1 --tags=update,molecule --args="--some --args -e"'

        self.loop.run_until_complete(self.handler.handle_message(room, event))

        key = "!room:id:@user:example.com"
        self.assertIn(key, self.handler.pending_confirmations)
        conf = self.handler.pending_confirmations[key]
        self.assertEqual(conf.get("tags"), "update,molecule")
        self.assertEqual(conf.get("arguments"), "--some --args -e")

    def test_execution_passes_options(self):
        # Seed a pending confirmation with tags/arguments and simulate reaction
        key = "!room:id:@user:example.com"
        self.handler.pending_confirmations[key] = {
            "project_id": 4,
            "template_id": 5,
            "template_name": "Template 5",
            "room_id": "!room:id",
            "sender": "@user:example.com",
            "timestamp": 0,
            "tags": "update,molecule",
            "arguments": "--limit web --check",
        }
        self.handler.confirmation_message_ids[key] = "evt1"
        self.mock_semaphore.start_task = AsyncMock(return_value={"id": 999})

        room = MagicMock(spec=MatrixRoom)
        room.room_id = "!room:id"

        self.loop.run_until_complete(
            self.handler.handle_reaction(room, "@user:example.com", "evt1", "👍")
        )

        self.mock_semaphore.start_task.assert_awaited()
        # Validate call included our options
        called_args, called_kwargs = self.mock_semaphore.start_task.call_args
        self.assertEqual(called_args[0:2], (4, 5))
        self.assertEqual(called_kwargs.get("tags"), "update,molecule")
        self.assertEqual(called_kwargs.get("arguments"), "--limit web --check")


if __name__ == "__main__":
    unittest.main()
