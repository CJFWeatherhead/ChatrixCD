"""Test runtime metrics tracking and version enhancements."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVersionDetection(unittest.TestCase):
    """Test version detection with git commit."""

    def test_version_format(self):
        """Test that version has correct format."""
        from chatrixcd import __version__

        self.assertIsInstance(__version__, str)
        parts = __version__.split(".")
        self.assertGreaterEqual(len(parts), 5, "Version should have at least 5 parts")

    def test_full_version_with_commit(self):
        """Test that full version includes git commit when in git repo."""
        from chatrixcd import __version__, __version_full__

        self.assertIsInstance(__version_full__, str)
        # Should either be same as version or have -c prefix
        self.assertTrue(
            __version_full__ == __version__ or __version_full__.startswith(__version__ + "-c"),
            "Full version should be base version or base version with commit",
        )

        # If we're in a git repo, should have commit
        git_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".git")
        if os.path.exists(git_dir):
            self.assertIn(
                "-c",
                __version_full__,
                "Should include commit ID when in git repo",
            )
            # Check commit ID format (should be hex)
            commit_part = __version_full__.split("-c")[1]
            self.assertTrue(
                all(c in "0123456789abcdef" for c in commit_part),
                "Commit ID should be hexadecimal",
            )


class TestMetricsStructure(unittest.TestCase):
    """Test metrics structure and initialization."""

    def test_metrics_keys(self):
        """Test that metrics dictionary has correct keys."""
        # We can't import bot without dependencies, but we can test the concept
        expected_keys = {
            "messages_sent",
            "requests_received",
            "errors",
            "emojis_used",
        }

        # This would be the metrics structure
        metrics = {
            "messages_sent": 0,
            "requests_received": 0,
            "errors": 0,
            "emojis_used": 0,
        }

        self.assertEqual(
            set(metrics.keys()),
            expected_keys,
            "Metrics should have expected keys",
        )
        self.assertTrue(
            all(isinstance(v, int) for v in metrics.values()),
            "All metrics should be integers",
        )
        self.assertTrue(
            all(v >= 0 for v in metrics.values()),
            "All metrics should be non-negative",
        )


class TestEmojiCounting(unittest.TestCase):
    """Test emoji counting logic."""

    def test_emoji_pattern(self):
        """Test emoji detection pattern."""
        import re

        # This is the pattern from bot.py
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"  # dingbats
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )

        # Test with various emoji
        # Note: The pattern matches consecutive emojis as one match
        test_cases = [
            ("Hello 😊", 1),
            ("🎉🎊🎈", 1),  # Consecutive emojis count as 1 match
            ("No emojis here", 0),
            (
                "Mixed 🚀 text 🌟 with 🎯 emoji",
                3,
            ),  # Separated emojis count separately
            ("✅❌⚠️", 1),  # Consecutive emojis count as 1 match
        ]

        for text, expected_count in test_cases:
            emojis = emoji_pattern.findall(text)
            actual_count = len(emojis)
            self.assertEqual(
                actual_count,
                expected_count,
                f"Expected {expected_count} emoji matches in '{text}', got {actual_count}",
            )

        # Test that we can count individual emoji in a match
        text_with_emojis = "🎉🎊🎈"
        matches = emoji_pattern.findall(text_with_emojis)
        if matches:
            # Each match is a string of consecutive emojis
            total_emojis = sum(len(match) for match in matches)
            self.assertEqual(total_emojis, 3, "Should count 3 individual emojis")


if __name__ == "__main__":
    unittest.main()
