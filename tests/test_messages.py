"""Tests for message manager module."""

import unittest
import os
import tempfile
import json
from chatrixcd.messages import MessageManager, DEFAULT_MESSAGES


class TestMessageManager(unittest.TestCase):
    """Test MessageManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.messages_file = os.path.join(self.temp_dir, "messages.json")

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temp files
        if os.path.exists(self.messages_file):
            os.remove(self.messages_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_init_with_nonexistent_file(self):
        """Test initialization with nonexistent file uses defaults."""
        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )
        self.assertEqual(manager.messages, DEFAULT_MESSAGES)

    def test_load_messages_from_file(self):
        """Test loading messages from file."""
        # Create a test messages file
        test_messages = {
            "greetings": ["Hello {name}!", "Hi {name}!"],
            "cancel": ["Cancelled!"],
        }

        with open(self.messages_file, "w") as f:
            json.dump(test_messages, f)

        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        # Should have merged with defaults
        self.assertIn("greetings", manager.messages)
        self.assertIn("cancel", manager.messages)
        # Custom greetings should override defaults
        self.assertEqual(
            manager.messages["greetings"], test_messages["greetings"]
        )
        # Default categories should still be present
        self.assertIn("brush_off", manager.messages)

    def test_get_random_message(self):
        """Test getting a random message from a category."""
        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        # Get a greeting
        greeting = manager.get_random_message(
            "greetings", name="@user:example.com"
        )

        # Should be a non-empty string
        self.assertIsInstance(greeting, str)
        self.assertGreater(len(greeting), 0)
        # Should have the name formatted in
        self.assertIn("user", greeting)

    def test_get_random_message_from_nonexistent_category(self):
        """Test getting message from nonexistent category."""
        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        message = manager.get_random_message("nonexistent_category")

        # Should return a placeholder
        self.assertIn("nonexistent_category", message)

    def test_get_all_messages(self):
        """Test getting all messages from a category."""
        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        greetings = manager.get_all_messages("greetings")

        # Should be a list
        self.assertIsInstance(greetings, list)
        self.assertGreater(len(greetings), 0)
        # Should be a copy (modifying shouldn't affect original)
        original_len = len(manager.messages["greetings"])
        greetings.append("New greeting")
        self.assertEqual(len(manager.messages["greetings"]), original_len)

    def test_check_for_changes(self):
        """Test checking for file modifications."""
        # Create a test messages file
        test_messages = {"greetings": ["Hello {name}!"]}

        with open(self.messages_file, "w") as f:
            json.dump(test_messages, f)

        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        # No changes yet (if auto_reload was True, FileWatcher would track this)
        # Without auto_reload, there's no file watcher
        self.assertIsNone(manager._file_watcher)

        # Modify the file
        import time

        time.sleep(0.1)  # Ensure mtime changes
        test_messages["greetings"].append("Hi {name}!")
        with open(self.messages_file, "w") as f:
            json.dump(test_messages, f)

        # Load messages again manually
        manager.load_messages()
        self.assertIn("Hi {name}!", manager.messages["greetings"])

    def test_message_formatting(self):
        """Test that messages are properly formatted with kwargs."""
        manager = MessageManager(
            messages_file=self.messages_file, auto_reload=False
        )

        # Get a message that uses formatting
        message = manager.get_random_message("pet")

        # Should be a valid message
        self.assertIsInstance(message, str)
        self.assertTrue(len(message) > 0)

    def test_default_messages_contain_all_categories(self):
        """Test that default messages contain all expected categories."""
        expected_categories = [
            "greetings",
            "brush_off",
            "cancel",
            "timeout",
            "task_start",
            "ping_success",
            "pet",
            "scold",
        ]

        for category in expected_categories:
            self.assertIn(category, DEFAULT_MESSAGES)
            self.assertIsInstance(DEFAULT_MESSAGES[category], list)
            self.assertGreater(len(DEFAULT_MESSAGES[category]), 0)


if __name__ == "__main__":
    unittest.main()
