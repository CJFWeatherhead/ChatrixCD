#!/bin/bash
# Script to integrate OIDC authentication plugin

echo "Applying OIDC plugin integration changes..."

# Change 1: Update bot.py login method signature
sed -i '' 's/async def login(self, oidc_token_callback=None) -> bool:/async def login(self) -> bool:/' chatrixcd/bot.py

# Change 2: Update bot.py login docstring
cat > /tmp/new_docstring.txt << 'EOF'
    async def login(self) -> bool:
        """Login to Matrix server using configured authentication method.
        
        Supports two authentication methods:
        1. Password authentication: Direct login with username/password (built-in)
        2. OIDC authentication: Interactive SSO login via oidc_auth plugin
        
        For OIDC, if a valid session is saved, it will be restored automatically
        without requiring interactive login. The oidc_auth plugin must be enabled.
        
        Returns:
            True if login successful, False otherwise
        """
EOF

# Change 3: Update OIDC authentication block in bot.py (line ~357)
# Find and replace the OIDC authentication call
python3 << 'PYTHON_SCRIPT'
import re

with open('chatrixcd/bot.py', 'r') as f:
    content = f.read()

# Replace the OIDC authentication call
old_pattern = r'(\s+)# OIDC authentication using Matrix SSO flow\s+return await self\._login_oidc\(token_callback=oidc_token_callback\)'

new_code = r'''\1# OIDC authentication - delegate to plugin if available
\1if hasattr(self, 'oidc_plugin') and self.oidc_plugin:
\1    logger.info("Using OIDC authentication plugin")
\1    return await self.oidc_plugin.login_oidc(self)
\1else:
\1    logger.error(
\1        "OIDC authentication requested but oidc_auth plugin is not loaded.\\n"
\1        "Please ensure the oidc_auth plugin is enabled in your configuration.\\n"
\1        "Alternatively, use password authentication by setting auth_type to 'password'."
\1    )
\1    return False'''

content = re.sub(old_pattern, new_code, content)

with open('chatrixcd/bot.py', 'w') as f:
    f.write(content)

print("Updated bot.py OIDC authentication block")
PYTHON_SCRIPT

# Change 4: Update main.py to register TUI app and remove temp OIDC callback
python3 << 'PYTHON_SCRIPT'
import re

with open('chatrixcd/main.py', 'r') as f:
    content = f.read()

# Remove the temporary OIDC callback function
old_callback = r'''    # Create OIDC callback that uses the TUI
    async def oidc_token_callback\(sso_url: str, redirect_url: str, identity_providers: list\) -> str:
        """TUI-based OIDC token input\..*?NotImplementedError\("OIDC authentication screen not yet implemented in new TUI\. Please use password authentication\."\)
    '''

new_code = '''    # Store reference to TUI app in bot for plugin access
    bot.tui_app = tui_app
    '''

content = re.sub(old_callback, new_code, content, flags=re.DOTALL)

# Update the login call to remove oidc_token_callback parameter
content = re.sub(
    r'login_success = await bot\.login\(oidc_token_callback=oidc_token_callback\)',
    'login_success = await bot.login()',
    content
)

with open('chatrixcd/main.py', 'w') as f:
    f.write(content)

print("Updated main.py")
PYTHON_SCRIPT

# Change 5: Update test files that reference oidc_token_callback
echo "Updating test files..."
find tests -name "*.py" -type f -exec sed -i '' 's/bot\.login(oidc_token_callback=mock_token_callback)/bot.login()/' {} \;

echo "OIDC plugin integration complete!"
echo ""
echo "The following changes have been made:"
echo "1. bot.login() no longer takes oidc_token_callback parameter"
echo "2. OIDC authentication now delegates to oidc_auth plugin"
echo "3. main.py stores TUI app reference in bot for plugin access"
echo "4. Tests updated to remove oidc_token_callback parameter"
echo ""
echo "To use OIDC authentication:"
echo "1. Set auth_type: 'oidc' in config.json"
echo "2. Ensure oidc_auth plugin is enabled (enabled by default)"
echo "3. Run chatrixcd normally"
