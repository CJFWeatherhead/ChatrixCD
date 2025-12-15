"""Tests for pet and scold command alias restrictions."""

import unittest
from chatrixcd.aliases import AliasManager


class TestPetScoldAliases(unittest.TestCase):
    """Test that pet and scold commands are properly protected."""

    def test_pet_is_reserved_command(self):
        """Test that 'pet' cannot be used as an alias (reserved command)."""
        import tempfile
        import os

        # Create a temporary file for aliases
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        temp_file.close()

        try:
            alias_manager = AliasManager(temp_file.name)

            # Try to add 'pet' as an alias - should fail
            result = alias_manager.add_alias("pet", "run 1 5")
            self.assertFalse(
                result,
                "Should not be able to alias 'pet' (it's a reserved command)",
            )

            # Verify it wasn't added
            self.assertIsNone(alias_manager.get_alias("pet"))
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)

    def test_scold_is_reserved_command(self):
        """Test that 'scold' cannot be used as an alias (reserved command)."""
        import tempfile
        import os

        # Create a temporary file for aliases
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        temp_file.close()

        try:
            alias_manager = AliasManager(temp_file.name)

            # Try to add 'scold' as an alias - should fail
            result = alias_manager.add_alias("scold", "status")
            self.assertFalse(
                result,
                "Should not be able to alias 'scold' (it's a reserved command)",
            )

            # Verify it wasn't added
            self.assertIsNone(alias_manager.get_alias("scold"))
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)

    def test_pet_is_valid_command(self):
        """Test that 'pet' is recognized as a valid command."""
        self.assertTrue(
            AliasManager.validate_command("pet"),
            "'pet' should be a valid command",
        )

    def test_scold_is_valid_command(self):
        """Test that 'scold' is recognized as a valid command."""
        self.assertTrue(
            AliasManager.validate_command("scold"),
            "'scold' should be a valid command",
        )

    def test_pet_with_args_is_valid_command(self):
        """Test that 'pet' with arguments is recognized as a valid command."""
        # Easter egg commands don't take arguments, but validate should still pass
        self.assertTrue(
            AliasManager.validate_command("pet extra args"),
            "'pet' with args should be valid (args are ignored)",
        )

    def test_scold_with_args_is_valid_command(self):
        """Test that 'scold' with arguments is recognized as a valid command."""
        # Easter egg commands don't take arguments, but validate should still pass
        self.assertTrue(
            AliasManager.validate_command("scold extra args"),
            "'scold' with args should be valid (args are ignored)",
        )


if __name__ == "__main__":
    unittest.main()
