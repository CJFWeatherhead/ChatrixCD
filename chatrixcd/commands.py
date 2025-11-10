"""Command handling for the bot."""

import html
import logging
import asyncio
import re
import platform
import socket
import psutil
from typing import Dict, Any, Optional, List
from nio import MatrixRoom, RoomMessageText
from chatrixcd.semaphore import SemaphoreClient
from chatrixcd.aliases import AliasManager
from chatrixcd.messages import MessageManager
from chatrixcd import __version__

logger = logging.getLogger(__name__)

class CommandHandler:
    """Handle bot commands."""

    def __init__(self, bot: Any, config: Dict[str, Any], semaphore: SemaphoreClient):
        """Initialize command handler.
        
        Args:
            bot: Reference to the bot instance
            config: Bot configuration
            semaphore: Semaphore client instance
        """
        self.bot = bot
        self.config = config
        self.semaphore = semaphore
        self.command_prefix = config.get('command_prefix', '!cd')
        self.allowed_rooms = config.get('allowed_rooms', [])
        self.admin_users = config.get('admin_users', [])
        
        # Track running tasks
        self.active_tasks: Dict[int, Dict[str, Any]] = {}
        
        # Track last task run (for status/logs without args)
        self.last_task_id: Optional[int] = None
        self.last_project_id: Optional[int] = None
        
        # Initialize alias manager with auto-reload
        self.alias_manager = AliasManager(auto_reload=True)
        
        # Initialize message manager with auto-reload
        self.message_manager = MessageManager(auto_reload=True)
        
        # Track pending confirmations for run commands
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        
        # Track message event IDs for threading reactions
        self.confirmation_message_ids: Dict[str, str] = {}
        
        # Track log tailing sessions: {room_id: {'task_id': int, 'project_id': int, 'last_log_size': int}}
        self.log_tailing_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Track global log tailing mode per room: {room_id: bool}
        self.global_log_tailing_enabled: Dict[str, bool] = {}

    def is_allowed_room(self, room_id: str) -> bool:
        """Check if bot is allowed to respond in this room.
        
        Args:
            room_id: Room ID to check
            
        Returns:
            True if allowed or no restrictions, False otherwise
        """
        if not self.allowed_rooms:
            return True
        return room_id in self.allowed_rooms

    def is_admin(self, user_id: str) -> bool:
        """Check if user is an admin.
        
        Handles URL-encoded usernames (e.g., @user%40domain.com).
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user is admin or no restrictions, False otherwise
        """
        if not self.admin_users:
            return True
        
        # URL decode both the incoming user_id and admin users for comparison
        import urllib.parse
        normalized_user_id = urllib.parse.unquote(user_id)
        
        # Check against all admin users (with normalization)
        for admin in self.admin_users:
            normalized_admin = urllib.parse.unquote(admin)
            if normalized_user_id == normalized_admin:
                return True
        
        return False

    def markdown_to_html(self, text: str) -> str:
        """Convert simple markdown to HTML for Matrix.
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            HTML formatted text
        """
        # Convert Matrix user mentions (@username:server.com) to HTML links for proper highlighting
        # This makes Matrix clients properly highlight the mentioned user
        # Matrix spec allows: lowercase letters, digits, hyphens, dots, underscores, equals, and plus
        text = re.sub(
            r'(@[a-zA-Z0-9._=+-]+:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'<a href="https://matrix.to/#/\1">\1</a>',
            text
        )
        
        # Convert bold **text** to <strong>text</strong>
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Convert italic *text* to <em>text</em>
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
        # Convert code `text` to <code>text</code>
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        # Convert bullet points • to <li>
        text = re.sub(r'• (.+?)(\n|$)', r'<li>\1</li>\2', text)
        # Wrap consecutive <li> items in <ul>
        text = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>{m.group(0)}</ul>', text, flags=re.DOTALL)
        # Convert line breaks to <br>
        text = text.replace('\n', '<br/>\n')
        return text
    
    def _colorize(self, text: str, color: str, bg_color: Optional[str] = None) -> str:
        """Add Matrix-compatible color to text using data-mx-color attribute.
        
        Args:
            text: Text to colorize
            color: Foreground color (hex format like #ff0000)
            bg_color: Optional background color (hex format)
            
        Returns:
            HTML span with color attributes
        """
        attributes = f'data-mx-color="{color}"'
        if bg_color:
            attributes += f' data-mx-bg-color="{bg_color}"'
        return f'<span {attributes}>{text}</span>'
    
    def _color_success(self, text: str) -> str:
        """Color text as success (green)."""
        return self._colorize(text, '#4e9a06')
    
    def _color_error(self, text: str) -> str:
        """Color text as error (red)."""
        return self._colorize(text, '#cc0000')
    
    def _color_warning(self, text: str) -> str:
        """Color text as warning (yellow)."""
        return self._colorize(text, '#c4a000')
    
    def _color_info(self, text: str) -> str:
        """Color text as info (blue)."""
        return self._colorize(text, '#3465a4')
    
    def _create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Create an HTML table for Matrix.
        
        Args:
            headers: List of column headers
            rows: List of rows, each row is a list of cell values
            
        Returns:
            HTML table string
        """
        # Start table with border
        table_html = '<table><thead><tr>'
        
        # Add headers
        for header in headers:
            table_html += f'<th>{html.escape(header)}</th>'
        table_html += '</tr></thead><tbody>'
        
        # Add rows
        for row in rows:
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td>{html.escape(str(cell))}</td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table>'
        return table_html

    def _get_display_name(self, user_id: str | None) -> str:
        """Get a friendly display name for a user.
        
        Returns the full Matrix ID for proper highlighting/mentions in messages.
        The markdown_to_html function will convert it to a clickable mention link.
        
        Args:
            user_id: User ID to get display name for, defaults to `'friend'` if `None` is passed
            
        Returns:
            Full Matrix user ID (e.g., @username:server.com) for proper mentions, or `'friend'` if `user_id` is `None`
        """
        # Return the full Matrix ID for proper mentions
        # The markdown_to_html function will convert it to an HTML link
        return user_id or "friend"
    
    def _get_greeting(self, user_id: str | None) -> str:
        """Get a random greeting for a user.
        
        Args:
            user_id: User ID to greet
            
        Returns:
            Random greeting with user's display name
        """
        name = self._get_display_name(user_id)
        return self.message_manager.get_random_message('greetings', name=name)

    async def handle_reaction(self, room: MatrixRoom, sender: str, event_id: str, reaction_key: str):
        """Handle a reaction to a message.
        
        Args:
            room: Room where reaction was sent
            sender: User who sent the reaction
            event_id: Event ID being reacted to
            reaction_key: The reaction emoji/key
        """
        # Check if this is a reaction to a confirmation message
        confirmation_key = None
        for key, msg_id in self.confirmation_message_ids.items():
            if msg_id == event_id:
                confirmation_key = key
                break
        
        if not confirmation_key:
            logger.debug(f"Reaction to non-confirmation message: {event_id}")
            return
        
        # Check if the confirmation still exists
        if confirmation_key not in self.pending_confirmations:
            logger.debug(f"Confirmation expired or already handled: {confirmation_key}")
            return
        
        confirmation = self.pending_confirmations[confirmation_key]
        
        # Only accept reactions from the original sender (for run/exit commands)
        if confirmation['sender'] != sender:
            # For other admins, they need to reply with a message, not a reaction
            logger.info(f"Ignoring reaction from {sender}, confirmation was initiated by {confirmation['sender']}")
            user_name = self._get_display_name(sender)
            await self.bot.send_message(
                room.room_id,
                f"{user_name} 👋 - Only {self._get_display_name(confirmation['sender'])} can react to this confirmation. Admins can reply with a message instead!"
            )
            return
        
        # Map reactions to confirmation responses
        positive_reactions = ['👍', '✅', '✓', '☑', '🆗', 'yes', 'y']
        negative_reactions = ['👎', '❌', '✖', '⛔', '🚫', 'no', 'n']
        
        # Strip variation selectors and zero-width characters that might be in emoji
        reaction_clean = ''.join(c for c in reaction_key if ord(c) < 0xFE00 or ord(c) > 0xFE0F)
        reaction_lower = reaction_clean.lower()
        
        if reaction_clean in positive_reactions or reaction_lower in positive_reactions:
            # Positive confirmation
            del self.pending_confirmations[confirmation_key]
            del self.confirmation_message_ids[confirmation_key]
            
            # Handle based on action type
            if confirmation.get('action') == 'exit':
                await self._execute_exit(room.room_id, sender)
            elif confirmation.get('action') == 'log_on':
                await self._execute_log_on(room.room_id, sender)
            elif confirmation.get('action') == 'log_off':
                await self._execute_log_off(room.room_id, sender)
            else:
                # Task execution
                await self._execute_task(room.room_id, confirmation)
                
        elif reaction_clean in negative_reactions or reaction_lower in negative_reactions:
            # Negative confirmation
            del self.pending_confirmations[confirmation_key]
            del self.confirmation_message_ids[confirmation_key]
            
            await self.bot.send_message(
                room.room_id,
                self.message_manager.get_random_message('cancel')
            )

    async def handle_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming message and process commands.
        
        Args:
            room: Room where message was sent
            event: Message event
        """
        message = event.body.strip()
        
        # Check for pending confirmations first
        confirmation_key = f"{room.room_id}:{event.sender}"
        if confirmation_key in self.pending_confirmations:
            logger.info(f"Processing confirmation response from {event.sender}: {message}")
            await self.handle_confirmation(room.room_id, event.sender, message)
            return
        
        # Check if message starts with command prefix
        if not message.startswith(self.command_prefix):
            return
        
        logger.info(f"Received command from {event.sender}: {message}")
            
        # Check if room is allowed
        if not self.is_allowed_room(room.room_id):
            logger.info(f"Ignoring command in non-allowed room: {room.room_id}")
            return
        
        # Check if user is admin (if admins are configured)
        if not self.is_admin(event.sender):
            # Send fun brush-off message
            response = self.message_manager.get_random_message('brush_off')
            logger.info(f"Non-admin user {event.sender} attempted command, sending: {response}")
            await self.bot.send_message(room.room_id, response)
            return
            
        # Parse command
        command_text = message[len(self.command_prefix):].strip()
        if not command_text:
            logger.info(f"Empty command from {event.sender}, sending help")
            await self.send_help(room.room_id, event.sender)
            return
        
        # Resolve aliases
        resolved_command = self.alias_manager.resolve_command(command_text)
        parts = resolved_command.split()
        
        command = parts[0].lower()
        args = parts[1:]
        
        logger.info(f"Executing command '{command}' with args {args} from {event.sender}")
        
        # Route to appropriate handler
        if command == 'help':
            await self.send_help(room.room_id, event.sender)
        elif command == 'admins':
            await self.list_admins(room.room_id, event.sender)
        elif command == 'rooms':
            await self.manage_rooms(room.room_id, args, event.sender)
        elif command == 'exit':
            await self.exit_bot(room.room_id, event.sender)
        elif command == 'projects':
            await self.list_projects(room.room_id, event.sender)
        elif command == 'templates':
            await self.list_templates(room.room_id, args, event.sender)
        elif command == 'run':
            await self.run_task(room.room_id, event.sender, args)
        elif command == 'status':
            await self.check_status(room.room_id, args, event.sender)
        elif command == 'stop':
            await self.stop_task(room.room_id, event.sender, args)
        elif command in ('logs', 'log'):
            await self.get_logs(room.room_id, args, event.sender)
        elif command == 'ping':
            await self.ping_semaphore(room.room_id, event.sender)
        elif command == 'info':
            await self.get_semaphore_info(room.room_id, event.sender)
        elif command == 'aliases':
            await self.list_command_aliases(room.room_id, event.sender)
        elif command == 'pet':
            await self.handle_pet(room.room_id, event.sender)
        elif command == 'scold':
            await self.handle_scold(room.room_id, event.sender)
        else:
            greeting = self._get_greeting(event.sender)
            response = f"{greeting} - Unknown command: {command}. Type '{self.command_prefix} help' for available commands."
            logger.info(f"Unknown command '{command}' from {event.sender}, sending: {response}")
            await self.bot.send_message(room.room_id, response)

    async def send_help(self, room_id: str, sender: str | None):
        """Send help message.
        
        Args:
            room_id: Room to send help to
            sender: User who requested help (for personalization)
        """
        greeting = self._get_greeting(sender)
        
        # Plain text version for clients without HTML support
        help_text = f"""{greeting} Here's what I can do for you! 🚀

**ChatrixCD Bot Commands** 📚

{self.command_prefix} help - Show this help message
{self.command_prefix} admins - List admin users
{self.command_prefix} rooms [join|part <room_id>] - List or manage rooms
{self.command_prefix} exit - Exit the bot (requires confirmation)
{self.command_prefix} projects - List available projects
{self.command_prefix} templates <project_id> - List templates for a project
{self.command_prefix} run <project_id> <template_id> - Run a task from template
{self.command_prefix} status [task_id] - Check status of a task (uses last task if no ID)
{self.command_prefix} stop <task_id> - Stop a running task
{self.command_prefix} logs [on|off|task_id] - Get/tail logs for a task (uses last task if no ID)
{self.command_prefix} ping - Ping Semaphore server
{self.command_prefix} info - Get Semaphore server info
{self.command_prefix} aliases - List command aliases

💡 **Tip:** You can react to confirmations with 👍/👎 instead of replying!
"""
        
        # HTML version with table
        greeting_html = self.markdown_to_html(greeting)
        
        # Create table for commands
        commands = [
            ['help', 'Show this help message', 'ℹ️'],
            ['admins', 'List admin users', '👑'],
            ['rooms [join|part <room_id>]', 'List or manage rooms', '🏠'],
            ['exit', 'Exit the bot (requires confirmation)', '🚪'],
            ['projects', 'List available projects', '📋'],
            ['templates <project_id>', 'List templates for a project', '📝'],
            ['run <project_id> <template_id>', 'Run a task from template', '🚀'],
            ['status [task_id]', 'Check task status (uses last task if no ID)', '📊'],
            ['stop <task_id>', 'Stop a running task', '🛑'],
            ['logs [on|off|task_id]', 'Get/tail task logs (uses last task if no ID)', '📋'],
            ['ping', 'Ping Semaphore server', '🏓'],
            ['info', 'Get Semaphore server and bot info', 'ℹ️'],
            ['aliases', 'List command aliases', '🔖'],
        ]
        
        rows_html = ''
        for cmd, desc, emoji in commands:
            rows_html += f'<tr><td><code>{self.command_prefix} {cmd}</code></td><td>{desc}</td><td>{emoji}</td></tr>'
        
        html_text = f"""{greeting_html} Here's what I can do for you! 🚀<br/><br/>
<strong>ChatrixCD Bot Commands</strong> 📚<br/><br/>
<table>
<thead><tr><th>Command</th><th>Description</th><th></th></tr></thead>
<tbody>{rows_html}</tbody>
</table><br/>
💡 <strong>Tip:</strong> You can react to confirmations with 👍/👎 instead of replying!
"""
        
        response_msg = f"Help requested by {sender}, sending response"
        logger.info(response_msg)
        await self.bot.send_message(room_id, help_text, html_text, msgtype="m.notice")

    async def list_admins(self, room_id: str, sender: str | None):
        """List admin users.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        greeting = self._get_greeting(sender)
        
        # Plain text version
        if not self.admin_users:
            message = f"{greeting} Here's the admin roster! 👑\n\n"
            message += "**Admin Users**\n\n"
            message += "No admin users configured. All users have admin access."
        else:
            message = f"{greeting} Here are the bot overlords! 👑\n\n"
            message += "**Admin Users**\n\n"
            for admin in self.admin_users:
                message += f"• {admin}\n"
        
        # HTML version with table
        greeting_html = self.markdown_to_html(greeting)
        
        if not self.admin_users:
            html_message = f"{greeting_html} Here's the admin roster! 👑<br/><br/><strong>Admin Users</strong><br/><br/>{self._color_info('ℹ️ No admin users configured. All users have admin access.')}"
        else:
            # Create table for admins
            table_html = '<table><thead><tr><th>Admin User</th></tr></thead><tbody>'
            for admin in self.admin_users:
                table_html += f'<tr><td>{html.escape(admin)}</td></tr>'
            table_html += '</tbody></table>'
            html_message = f"{greeting_html} Here are the bot overlords! 👑<br/><br/><strong>Admin Users</strong><br/><br/>{table_html}"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")
    
    async def _list_rooms(self, room_id: str, user_name: str):
        """List all rooms the bot is in.
        
        Args:
            room_id: Room to send response to
            user_name: Display name of requesting user
        """
        rooms = self.bot.client.rooms
        if not rooms:
            plain_msg = f"{user_name} 👋 - Not currently in any rooms. 🏠"
            html_msg = self.markdown_to_html(plain_msg)
            await self.bot.send_message(room_id, plain_msg, html_msg, msgtype="m.notice")
            return
        
        # Plain text version
        message = f"{user_name} 👋 Here's where I hang out! 🏠\n\n"
        message += "**Rooms I'm In**\n\n"
        for room_id_key, room in rooms.items():
            room_name = room.display_name or "Unknown"
            message += f"• **{room_name}**\n  `{room_id_key}`\n"
        
        # HTML version with table
        greeting_html = self.markdown_to_html(user_name)
        table_html = '<table><thead><tr><th>Room Name</th><th>Room ID</th></tr></thead><tbody>'
        for room_id_key, room in rooms.items():
            room_name = html.escape(room.display_name or "Unknown")
            table_html += f'<tr><td><strong>{room_name}</strong></td><td><code>{html.escape(room_id_key)}</code></td></tr>'
        table_html += '</tbody></table>'
        
        html_message = f"{greeting_html} 👋 Here's where I hang out! 🏠<br/><br/><strong>Rooms I'm In</strong><br/><br/>{table_html}"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")

    async def _join_room(self, room_id: str, user_name: str, target_room_id: str):
        """Join a room.
        
        Args:
            room_id: Room to send response to
            user_name: Display name of requesting user
            target_room_id: Room ID to join
        """
        try:
            await self.bot.client.join(target_room_id)
            await self.bot.send_message(room_id, f"✅ Joined room: {target_room_id}")
        except Exception as e:
            logger.error(f"Failed to join room {target_room_id}: {e}")
            await self.bot.send_message(room_id, f"❌ Failed to join room: {e}")

    async def _leave_room(self, room_id: str, user_name: str, target_room_id: str):
        """Leave a room.
        
        Args:
            room_id: Room to send response to
            user_name: Display name of requesting user
            target_room_id: Room ID to leave
        """
        try:
            await self.bot.client.room_leave(target_room_id)
            await self.bot.send_message(room_id, f"👋 Left room: {target_room_id}")
        except Exception as e:
            logger.error(f"Failed to leave room {target_room_id}: {e}")
            await self.bot.send_message(room_id, f"❌ Failed to leave room: {e}")

    async def manage_rooms(self, room_id: str, args: list, sender: str | None):
        """Manage bot rooms (list, join, part).
        
        Args:
            room_id: Room to send response to
            args: Command arguments (action, optional room_id)
            sender: User who sent the command
        """
        user_name = self._get_display_name(sender)
        
        # List rooms if no action specified
        if not args:
            await self._list_rooms(room_id, user_name)
            return
        
        action = args[0].lower()
        
        # Join room
        if action == 'join':
            if len(args) < 2:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} rooms join <room_id>"
                )
                return
            await self._join_room(room_id, user_name, args[1])
        
        # Leave room
        elif action in ('part', 'leave'):
            if len(args) < 2:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} rooms part <room_id>"
                )
                return
            await self._leave_room(room_id, user_name, args[1])
        
        # Unknown action
        else:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Unknown action: {action}. Use 'join' or 'part'."
            )
    
    async def exit_bot(self, room_id: str, sender: str):
        """Exit the bot with confirmation.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
        """
        user_name = self._get_display_name(sender)
        # Create a special confirmation for exit
        confirmation_key = f"{room_id}:{sender}"
        
        # Check if already waiting for confirmation
        if confirmation_key in self.pending_confirmations and self.pending_confirmations[confirmation_key].get('action') == 'exit':
            # User is confirming
            del self.pending_confirmations[confirmation_key]
            if confirmation_key in self.confirmation_message_ids:
                del self.confirmation_message_ids[confirmation_key]
            
            logger.info(f"Exit confirmed by {sender}")
            await self._execute_exit(room_id, sender)
        else:
            # Request confirmation
            self.pending_confirmations[confirmation_key] = {
                'action': 'exit',
                'room_id': room_id,
                'sender': sender,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            message = f"{user_name} 👋 - ⚠️ <strong>Confirm Bot Shutdown</strong>\n\n"
            message += "Are you sure you want to shut down the bot?\n\n"
            message += f"Reply with `{self.command_prefix} exit` again to confirm.\n"
            message += "Or react with 👍 to confirm or 👎 to cancel!"
            
            logger.info(f"Exit requested by {sender}, requesting confirmation")
            event_id = await self.bot.send_message(room_id, message)
            
            # Track the message ID for reaction handling
            if event_id:
                self.confirmation_message_ids[confirmation_key] = event_id
            
            # Set timeout to clear confirmation after 30 seconds
            asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 30, room_id))

    async def list_projects(self, room_id: str, sender: str | None):
        """List available Semaphore projects.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        projects = await self.semaphore.get_projects()
        user_name = self._get_display_name(sender)
        
        if not projects:
            # Check if this is an empty list (successful connection) or an error
            # Empty list means successful connection but no projects
            plain_msg = f"{user_name} 👋 - No projects found. Create a project in Semaphore UI first! 📋"
            html_msg = self.markdown_to_html(plain_msg)
            await self.bot.send_message(
                room_id,
                plain_msg,
                html_msg,
                msgtype="m.notice"
            )
            return
        
        # Plain text version
        message = f"{user_name} 👋 Here's what we can work with! 📋\n\n"
        message += "**Available Projects:**\n\n"
        for project in projects:
            name = project.get('name')
            proj_id = project.get('id')
            message += f"• **{name}** (ID: {proj_id})\n"
        
        # HTML version with table
        greeting_html = self.markdown_to_html(user_name)
        table_html = '<table><thead><tr><th>Project Name</th><th>ID</th></tr></thead><tbody>'
        for project in projects:
            name = html.escape(project.get('name', ''))
            proj_id = project.get('id', '')
            table_html += f'<tr><td><strong>{name}</strong></td><td>{proj_id}</td></tr>'
        table_html += '</tbody></table>'
        
        html_message = f"{greeting_html} 👋 Here's what we can work with! 📋<br/><br/><strong>Available Projects:</strong><br/><br/>{table_html}"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")

    def _format_description(self, description: str) -> str:
        """Format a description by parsing ¶ as paragraph breaks and markdown.
        
        Args:
            description: Raw description text
            
        Returns:
            Formatted description with paragraph breaks
        """
        if not description:
            return description
        
        # Replace ¶ with double newlines for paragraph breaks
        formatted = description.replace('¶', '\n\n')
        
        return formatted

    async def list_templates(self, room_id: str, args: list, sender: str | None):
        """List templates for a project.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (project_id)
            sender: User who requested the list
        """
        user_name = self._get_display_name(sender)
        
        # If no args, try to get the only project if there's only one
        if not args:
            projects = await self.semaphore.get_projects()
            if len(projects) == 1:
                project_id = projects[0].get('id')
                logger.info(f"Auto-selecting only available project: {project_id}")
            else:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} templates <project_id>\n\n"
                    f"Use `{self.command_prefix} projects` to list available projects."
                    
                )
                return
        else:
            try:
                project_id = int(args[0])
            except ValueError:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Invalid project ID ❌"
                    
                )
                return
            
        templates = await self.semaphore.get_project_templates(project_id)
        
        if not templates:
            plain_msg = f"{user_name} 👋 - No templates found for project {project_id} ❌"
            html_msg = self.markdown_to_html(plain_msg.replace('❌', self._color_error('❌')))
            await self.bot.send_message(
                room_id,
                plain_msg,
                html_msg,
                msgtype="m.notice"
            )
            return
        
        # Plain text version
        message = f"{user_name} 👋 Here are the templates for project {project_id}! 📝\n\n"
        message += "**Templates:**\n\n"
        for template in templates:
            message += f"• **{template.get('name')}** (ID: {template.get('id')})\n"
            if template.get('description'):
                desc = self._format_description(template.get('description'))
                message += f"  {desc}\n"
        
        # HTML version with table
        greeting_html = self.markdown_to_html(user_name)
        table_html = '<table><thead><tr><th>Template Name</th><th>ID</th><th>Description</th></tr></thead><tbody>'
        for template in templates:
            name = html.escape(template.get('name', ''))
            temp_id = template.get('id', '')
            desc = html.escape(self._format_description(template.get('description', 'No description')))
            table_html += f'<tr><td><strong>{name}</strong></td><td>{temp_id}</td><td>{desc}</td></tr>'
        table_html += '</tbody></table>'
        
        html_message = f"{greeting_html} 👋 Here are the templates for project {project_id}! 📝<br/><br/><strong>Templates:</strong><br/><br/>{table_html}"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")

    async def _resolve_run_task_params(self, room_id: str, sender: str, args: list) -> tuple:
        """Resolve project_id and template_id from args with smart auto-selection.
        
        Returns:
            Tuple of (project_id, template_id) or (None, None) if resolution failed
            (also sends error message to room if failed)
        """
        user_name = self._get_display_name(sender)
        
        # No args - try auto-selection
        if len(args) == 0:
            projects = await self.semaphore.get_projects()
            if len(projects) != 1:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} run <project_id> <template_id>\n\n"
                    f"Use `{self.command_prefix} projects` to list available projects."
                )
                return None, None
            
            project_id = projects[0].get('id')
            templates = await self.semaphore.get_project_templates(project_id)
            
            if len(templates) == 0:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No templates found for project {project_id}.\n"
                    f"Create a template in Semaphore UI first!"
                )
                return None, None
            elif len(templates) > 1:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Multiple templates available for project {project_id}.\n"
                    f"Use `{self.command_prefix} templates {project_id}` to list them."
                )
                return None, None
            
            template_id = templates[0].get('id')
            logger.info(f"Auto-selected project {project_id} and template {template_id}")
            return project_id, template_id
        
        # Only project_id provided
        if len(args) == 1:
            try:
                project_id = int(args[0])
            except ValueError:
                await self.bot.send_message(room_id, f"{user_name} 👋 - Invalid project ID ❌")
                return None, None
            
            templates = await self.semaphore.get_project_templates(project_id)
            
            if len(templates) == 0:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No templates found for project {project_id}.\n"
                    f"Create a template in Semaphore UI first!"
                )
                return None, None
            elif len(templates) > 1:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Multiple templates available for project {project_id}.\n"
                    f"Use `{self.command_prefix} templates {project_id}` to list them."
                )
                return None, None
            
            template_id = templates[0].get('id')
            logger.info(f"Auto-selected template {template_id}")
            return project_id, template_id
        
        # Both params provided
        if len(args) >= 2:
            try:
                project_id = int(args[0])
                template_id = int(args[1])
                return project_id, template_id
            except ValueError:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Invalid project or template ID ❌"
                )
                return None, None
        
        # Fallback
        await self.bot.send_message(
            room_id,
            f"{user_name} 👋 - Usage: {self.command_prefix} run <project_id> <template_id>"
        )
        return None, None

    async def run_task(self, room_id: str, sender: str, args: list):
        """Run a task from a template.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
            args: Command arguments (project_id, template_id)
        """
        user_name = self._get_display_name(sender)
        
        # Resolve parameters with smart auto-selection
        project_id, template_id = await self._resolve_run_task_params(room_id, sender, args)
        if project_id is None:
            return
        
        # Fetch template details for confirmation
        templates = await self.semaphore.get_project_templates(project_id)
        template = next((t for t in templates if t.get('id') == template_id), None)
        
        if not template:
            logger.info(f"Template {template_id} not found in project {project_id}")
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Template {template_id} not found in project {project_id} ❌"
            )
            return
        
        template_name = template.get('name', f'Template {template_id}')
        template_desc = self._format_description(template.get('description', 'No description'))
        
        # Request confirmation
        confirmation_key = f"{room_id}:{sender}"
        self.pending_confirmations[confirmation_key] = {
            'project_id': project_id,
            'template_id': template_id,
            'template_name': template_name,
            'room_id': room_id,
            'sender': sender,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        logger.info(f"Task run requested: project={project_id}, template={template_id} ({template_name}) by {sender}")
        
        message = f"{user_name} 👋 Ready to launch! ⚠️\n\n"
        message += f"**Confirm Task Execution**\n\n"
        message += f"**Template:** {template_name}\n"
        message += f"**Description:** {template_desc}\n"
        message += f"**Project ID:** {project_id}\n"
        message += f"**Template ID:** {template_id}\n\n"
        message += "Reply with **y**, **yes**, **go**, or **start** to confirm.\n"
        message += "Reply with **n**, **no**, **cancel**, or **stop** to cancel.\n"
        message += "Or react with 👍 to confirm or 👎 to cancel!"
        
        html_message = self.markdown_to_html(message)
        event_id = await self.bot.send_message(room_id, message, html_message)
        
        if event_id:
            self.confirmation_message_ids[confirmation_key] = event_id
        
        asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 300, room_id))

    async def _clear_confirmation_timeout(self, confirmation_key: str, timeout: int, room_id: str | None):
        """Clear a pending confirmation after timeout.
        
        Args:
            confirmation_key: The confirmation key
            timeout: Timeout in seconds
            room_id: Optional room ID to send timeout message to
        """
        await asyncio.sleep(timeout)
        if confirmation_key in self.pending_confirmations:
            del self.pending_confirmations[confirmation_key]
            logger.info(f"Cleared confirmation timeout for {confirmation_key}")
            
            # Send timeout message with fun response
            if room_id:
                await self.bot.send_message(room_id, self.message_manager.get_random_message('timeout'))

    async def _execute_exit(self, room_id: str, sender: str):
        """Execute bot exit.
        
        Args:
            room_id: Room ID
            sender: User ID
        """
        await self.bot.send_message(
            room_id,
            "👋 Shutting down bot as requested. Goodbye!"
        )
        
        # Give time for message to send
        await asyncio.sleep(1)
        
        # Trigger shutdown
        logger.info(f"Bot shutdown requested by {sender}")
        # Signal bot to close
        asyncio.create_task(self.bot.close())
        
        # Exit the event loop to shutdown
        import sys
        sys.exit(0)

    async def _execute_log_on(self, room_id: str, sender: str):
        """Execute global log tailing enable.
        
        Args:
            room_id: Room ID
            sender: User ID
        """
        user_name = self._get_display_name(sender)
        
        # Enable global log tailing for this room
        self.global_log_tailing_enabled[room_id] = True
        
        logger.info(f"Global log tailing enabled in room {room_id} by {sender}")
        message = f"{user_name} 👋 - ✅ **Global log tailing enabled!**\n\n"
        message += "Logs will be automatically streamed for all tasks that run in this room.\n"
        message += f"Use `{self.command_prefix} log off` to disable."
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
        
        # If there's already a task running, start tailing it
        if self.last_task_id is not None and self.last_task_id in self.active_tasks:
            task_info = self.active_tasks[self.last_task_id]
            project_id = task_info['project_id']
            task_name = task_info.get('template_name')
            task_display = f"{task_name} ({self.last_task_id})" if task_name else str(self.last_task_id)
            
            # Start tailing the current task
            self.log_tailing_sessions[room_id] = {
                'task_id': self.last_task_id,
                'project_id': project_id,
                'last_log_size': 0
            }
            
            start_message = f"📋 Starting log stream for task **{task_display}**..."
            await self.bot.send_message(room_id, start_message, self.markdown_to_html(start_message))
            
            # Start the tailing task
            asyncio.create_task(self.tail_logs(room_id, self.last_task_id, project_id))

    async def _execute_log_off(self, room_id: str, sender: str):
        """Execute global log tailing disable.
        
        Args:
            room_id: Room ID
            sender: User ID
        """
        user_name = self._get_display_name(sender)
        
        # Disable global log tailing for this room
        self.global_log_tailing_enabled[room_id] = False
        
        # Stop any active tailing session
        if room_id in self.log_tailing_sessions:
            task_id = self.log_tailing_sessions[room_id]['task_id']
            del self.log_tailing_sessions[room_id]
            logger.info(f"Stopped log tailing for task {task_id} in room {room_id}")
        
        logger.info(f"Global log tailing disabled in room {room_id} by {sender}")
        message = f"{user_name} 👋 - 🛑 **Global log tailing disabled!**\n\n"
        message += "You will no longer receive automatic log streams for tasks.\n"
        message += f"Use `{self.command_prefix} log on` to re-enable."
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)


    async def _execute_task(self, room_id: str, confirmation: Dict[str, Any]):
        """Execute a task based on confirmation.
        
        Args:
            room_id: Room ID
            confirmation: Confirmation details
        """
        project_id = confirmation['project_id']
        template_id = confirmation['template_id']
        template_name = confirmation['template_name']
        sender = confirmation['sender']
        
        start_message = self.message_manager.get_random_message('task_start', task_name=template_name)
        html_start_message = self.markdown_to_html(start_message)
        logger.info(f"Executing task: project={project_id}, template={template_id} ({template_name}), sending: {start_message}")
        await self.bot.send_message(room_id, start_message, html_start_message)
        
        task = await self.semaphore.start_task(project_id, template_id)
        
        if not task:
            logger.error(f"Failed to start task for project {project_id}, template {template_id}")
            await self.bot.send_message(
                room_id,
                "Failed to start task ❌"
                
            )
            return
        
        task_id = task.get('id')
        self.active_tasks[task_id] = {
            'project_id': project_id,
            'room_id': room_id,
            'sender': sender,
            'task': task,
            'template_name': template_name
        }
        
        # Track as last task
        self.last_task_id = task_id
        self.last_project_id = project_id
        
        message_text = f"✅ Task **{template_name} ({task_id})** started successfully!\n"
        message_text += f"Use `{self.command_prefix} status` to check progress."
        html_message = self.markdown_to_html(message_text)
        logger.info(f"Task started successfully: task_id={task_id}, sending: {message_text}")
        await self.bot.send_message(room_id, message_text, html_message)
        
        # Start monitoring the task
        asyncio.create_task(self.monitor_task(project_id, task_id, room_id, template_name))

    async def handle_confirmation(self, room_id: str, sender: str, message: str):
        """Handle confirmation response for task execution.
        
        Args:
            room_id: Room ID
            sender: User ID
            message: Response message
        """
        confirmation_key = f"{room_id}:{sender}"
        if confirmation_key not in self.pending_confirmations:
            return
        
        confirmation = self.pending_confirmations[confirmation_key]
        del self.pending_confirmations[confirmation_key]
        
        # Clean up message ID tracking
        if confirmation_key in self.confirmation_message_ids:
            del self.confirmation_message_ids[confirmation_key]
        
        # Check if message is a confirmation
        confirm_words = ['y', 'yes', 'go', 'start', 'ok', '👍', '✓', '✅']
        cancel_words = ['n', 'no', 'cancel', 'stop', 'end', 'nope', '👎', '❌', '✖']
        
        message_lower = message.strip().lower()
        is_confirmed = message_lower in confirm_words
        is_cancelled = message_lower in cancel_words
        
        if is_cancelled:
            await self.bot.send_message(
                room_id,
                self.message_manager.get_random_message('cancel')
                
            )
            return
        
        if not is_confirmed:
            await self.bot.send_message(
                room_id,
                "Task execution cancelled. ❌"
                
            )
            return
        
        # Check if this is an exit confirmation
        if confirmation.get('action') == 'exit':
            await self._execute_exit(room_id, sender)
        elif confirmation.get('action') == 'log_on':
            await self._execute_log_on(room_id, sender)
        elif confirmation.get('action') == 'log_off':
            await self._execute_log_off(room_id, sender)
        else:
            # Execute the task
            await self._execute_task(room_id, confirmation)

    async def monitor_task(self, project_id: int, task_id: int, room_id: str, task_name: str | None):
        """Monitor a task and report status updates.
        
        Args:
            project_id: Project ID
            task_id: Task ID
            room_id: Room to send updates to
            task_name: Optional task name
        """
        logger.info(f"Monitoring task {task_id}")
        last_status = None
        last_notification_time = asyncio.get_event_loop().time()
        notification_interval = 300  # 5 minutes
        
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        
        while task_id in self.active_tasks:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            task = await self.semaphore.get_task_status(project_id, task_id)
            if not task:
                continue
                
            status = task.get('status')
            current_time = asyncio.get_event_loop().time()
            
            if status != last_status:
                logger.info(f"Task {task_id} status changed: {last_status} -> {status}")
                last_status = status
                last_notification_time = current_time
                
                if status == 'running':
                    message = f"🔄 Task **{task_display}** is now running..."
                    html_message = self.markdown_to_html(message)
                    await self.bot.send_message(room_id, message, html_message)
                    
                    # Start log tailing if global log tailing is enabled for this room
                    if self.global_log_tailing_enabled.get(room_id, False) and room_id not in self.log_tailing_sessions:
                        logger.info(f"Auto-starting log tailing for task {task_id} (global log tailing enabled)")
                        self.log_tailing_sessions[room_id] = {
                            'task_id': task_id,
                            'project_id': project_id,
                            'last_log_size': 0
                        }
                        
                        log_message = f"📋 Starting log stream for task **{task_display}**..."
                        await self.bot.send_message(room_id, log_message, self.markdown_to_html(log_message))
                        
                        # Start the tailing task
                        asyncio.create_task(self.tail_logs(room_id, task_id, project_id))
                elif status == 'success':
                    # Get the user who initiated this task
                    task_sender = self.active_tasks[task_id].get('sender')
                    sender_name = self._get_display_name(task_sender) if task_sender else "there"
                    
                    message = f"{sender_name} 👋 Your task **{task_display}** completed successfully! ✅"
                    html_message = self.markdown_to_html(message)
                    event_id = await self.bot.send_message(room_id, message, html_message)
                    # React with party emoji
                    if event_id:
                        await self.bot.send_reaction(room_id, event_id, "🎉")
                    del self.active_tasks[task_id]
                    break
                elif status in ('error', 'stopped'):
                    # Get the user who initiated this task
                    task_sender = self.active_tasks[task_id].get('sender')
                    sender_name = self._get_display_name(task_sender) if task_sender else "there"
                    
                    message = f"{sender_name} 👋 Task **{task_display}** failed or was stopped. Status: {status} ❌"
                    html_message = self.markdown_to_html(message)
                    await self.bot.send_message(room_id, message, html_message)
                    del self.active_tasks[task_id]
                    break
            elif status == 'running' and (current_time - last_notification_time) >= notification_interval:
                # Send periodic update for long-running tasks
                message = f"⏳ Task **{task_display}** is still running..."
                html_message = self.markdown_to_html(message)
                await self.bot.send_message(room_id, message, html_message)
                last_notification_time = current_time

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for task status.
        
        Args:
            status: Task status string
            
        Returns:
            Emoji string representing the status
        """
        return {
            'waiting': '⏸️',
            'running': '🔄',
            'success': '✅',
            'error': '❌',
            'stopped': '🛑',
            'skipped': '⏭️',
            'rescued': '🛟',
            'ignored': '🙈',
            'unreachable': '🔒',
            'unknown': '❓'
        }.get(status, '❓')

    def _color_status(self, status: str, emoji: str) -> str:
        """Apply color to status based on type.
        
        Args:
            status: Task status string
            emoji: Emoji for the status
            
        Returns:
            HTML string with colored status
        """
        if status == 'success':
            return self._color_success(f'{emoji} {status}')
        elif status in ('error', 'stopped'):
            return self._color_error(f'{emoji} {status}')
        elif status == 'running':
            return self._color_info(f'{emoji} {status}')
        elif status == 'waiting':
            return self._color_warning(f'{emoji} {status}')
        else:
            return f'{emoji} {status}'

    async def check_status(self, room_id: str, args: list, sender: str | None):
        """Check status of a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id) - optional
            sender: User who requested the status
        """
        user_name = self._get_display_name(sender)
        
        # Determine task ID
        if not args:
            if self.last_task_id is None:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No task ID provided and no previous task found.\n"
                    f"Usage: {self.command_prefix} status <task_id>"
                )
                return
            task_id = self.last_task_id
            project_id = self.last_project_id
            logger.info(f"Using last task ID: {task_id}")
        else:
            try:
                task_id = int(args[0])
            except ValueError:
                await self.bot.send_message(room_id, f"{user_name} 👋 - Invalid task ID ❌")
                return
            
            if task_id not in self.active_tasks:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Task {task_id} not found in active tasks ❌"
                )
                return
            
            project_id = self.active_tasks[task_id]['project_id']
        
        # Get task status
        task = await self.semaphore.get_task_status(project_id, task_id)
        if not task:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Could not get status for task {task_id} ❌"
            )
            return
        
        status = task.get('status', 'unknown')
        task_name = self.active_tasks.get(task_id, {}).get('template_name')
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        status_emoji = self._get_status_emoji(status)
        
        # Build plain text message
        message = f"{user_name} 👋 Here's the scoop! {status_emoji}\n\n"
        message += f"**Task {task_display} Status:** {status}\n\n"
        if task.get('start'):
            message += f"**Started:** {task.get('start')}\n"
        if task.get('end'):
            message += f"**Ended:** {task.get('end')}\n"
        
        # Build HTML message with colored status
        greeting_html = self.markdown_to_html(user_name)
        status_colored = self._color_status(status, status_emoji)
        
        html_message = f"{greeting_html} 👋 Here's the scoop!<br/><br/>"
        html_message += f"<strong>Task {html.escape(task_display)} Status:</strong> {status_colored}<br/><br/>"
        if task.get('start'):
            html_message += f"<strong>Started:</strong> {html.escape(str(task.get('start')))}<br/>"
        if task.get('end'):
            html_message += f"<strong>Ended:</strong> {html.escape(str(task.get('end')))}<br/>"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")

    async def stop_task(self, room_id: str, sender: str, args: list):
        """Stop a running task.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
            args: Command arguments (task_id)
        """
        user_name = self._get_display_name(sender)
        
        if not args:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Usage: {self.command_prefix} stop <task_id>"
                
            )
            return
            
        try:
            task_id = int(args[0])
        except ValueError:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Invalid task ID ❌"
                
            )
            return
            
        if task_id not in self.active_tasks:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Task {task_id} not found in active tasks ❌"
                
            )
            return
            
        project_id = self.active_tasks[task_id]['project_id']
        task_name = self.active_tasks[task_id].get('template_name')
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        
        success = await self.semaphore.stop_task(project_id, task_id)
        
        if success:
            message = f"{user_name} 👋 - 🛑 Task **{task_display}** stopped"
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
            del self.active_tasks[task_id]
        else:
            message = f"{user_name} 👋 - ❌ Failed to stop task **{task_display}**"
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)

    async def _handle_log_tailing_on(self, room_id: str, sender: str) -> bool:
        """Handle log tailing ON command with confirmation.
        
        Args:
            room_id: Room ID
            sender: User who sent command
            
        Returns:
            True if this was a confirmation request, False if already confirmed
        """
        user_name = self._get_display_name(sender)
        confirmation_key = f"{room_id}:{sender}"
        
        # Check if already waiting for confirmation
        if confirmation_key in self.pending_confirmations and self.pending_confirmations[confirmation_key].get('action') == 'log_on':
            # User is confirming
            del self.pending_confirmations[confirmation_key]
            if confirmation_key in self.confirmation_message_ids:
                del self.confirmation_message_ids[confirmation_key]
            
            logger.info(f"Log tailing 'on' confirmed by {sender}")
            await self._execute_log_on(room_id, sender)
            return False
        else:
            # Request confirmation
            self.pending_confirmations[confirmation_key] = {
                'action': 'log_on',
                'room_id': room_id,
                'sender': sender,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            message = f"{user_name} 👋 - ⚠️ **Enable Global Log Tailing**\n\n"
            message += "This will enable automatic log tailing for all tasks in this room.\n"
            message += "Logs will be streamed in real-time as tasks run.\n\n"
            message += f"Reply with `{self.command_prefix} log on` again to confirm.\n"
            message += "Or react with 👍 to confirm or 👎 to cancel!"
            
            logger.info(f"Log tailing 'on' requested by {sender}, requesting confirmation")
            event_id = await self.bot.send_message(room_id, message)
            
            if event_id:
                self.confirmation_message_ids[confirmation_key] = event_id
            
            asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 30, room_id))
            return True

    async def _handle_log_tailing_off(self, room_id: str, sender: str) -> bool:
        """Handle log tailing OFF command with confirmation.
        
        Args:
            room_id: Room ID
            sender: User who sent command
            
        Returns:
            True if this was a confirmation request, False if already confirmed
        """
        user_name = self._get_display_name(sender)
        confirmation_key = f"{room_id}:{sender}"
        
        # Check if already waiting for confirmation
        if confirmation_key in self.pending_confirmations and self.pending_confirmations[confirmation_key].get('action') == 'log_off':
            # User is confirming
            del self.pending_confirmations[confirmation_key]
            if confirmation_key in self.confirmation_message_ids:
                del self.confirmation_message_ids[confirmation_key]
            
            logger.info(f"Log tailing 'off' confirmed by {sender}")
            await self._execute_log_off(room_id, sender)
            return False
        else:
            # Check if log tailing is even enabled
            if not self.global_log_tailing_enabled.get(room_id, False):
                logger.info(f"Log tailing 'off' requested but not enabled in room {room_id}")
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Global log tailing is not currently enabled."
                )
                return True
            
            # Request confirmation
            self.pending_confirmations[confirmation_key] = {
                'action': 'log_off',
                'room_id': room_id,
                'sender': sender,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            message = f"{user_name} 👋 - ⚠️ **Disable Global Log Tailing**\n\n"
            message += "This will disable automatic log tailing for all tasks in this room.\n"
            message += "You will stop receiving real-time log updates.\n\n"
            message += f"Reply with `{self.command_prefix} log off` again to confirm.\n"
            message += "Or react with 👍 to confirm or 👎 to cancel!"
            
            logger.info(f"Log tailing 'off' requested by {sender}, requesting confirmation")
            event_id = await self.bot.send_message(room_id, message)
            
            if event_id:
                self.confirmation_message_ids[confirmation_key] = event_id
            
            asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 30, room_id))
            return True

    async def _retrieve_task_logs(self, room_id: str, args: list, sender: str | None):
        """Retrieve and display logs for a specific task.
        
        Args:
            room_id: Room ID
            args: Command arguments (empty for last task, or task_id)
            sender: User who requested logs
        """
        user_name = self._get_display_name(sender)
        
        # Determine task ID
        if not args:
            if self.last_task_id is None:
                logger.info(f"Log request with no args and no last task")
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No task ID provided and no previous task found.\n"
                    f"Usage: {self.command_prefix} log [on|off|task_id]"
                )
                return
            task_id = self.last_task_id
            project_id = self.last_project_id
            logger.info(f"Using last task ID for logs: {task_id}")
        else:
            try:
                task_id = int(args[0])
            except ValueError:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Invalid task ID ❌\n"
                    f"Usage: {self.command_prefix} log [on|off|task_id]"
                )
                return
            
            # Try to find project ID
            if task_id in self.active_tasks:
                project_id = self.active_tasks[task_id]['project_id']
            elif self.last_task_id == task_id and self.last_project_id is not None:
                project_id = self.last_project_id
            else:
                # Try to get project_id from semaphore
                try:
                    task_info = await self.semaphore.get_task(task_id)
                    project_id = task_info.get('project_id')
                    if not project_id:
                        await self.bot.send_message(
                            room_id,
                            f"{user_name} 👋 - Could not find project for task {task_id} ❌"
                        )
                        return
                except Exception as e:
                    logger.error(f"Failed to get task info for {task_id}: {e}")
                    await self.bot.send_message(
                        room_id,
                        f"{user_name} 👋 - Could not retrieve task info ❌"
                    )
                    return
        
        # Get and display logs
        try:
            logs = await self.semaphore.get_task_output(project_id, task_id)
            if logs:
                formatted_logs = self._format_task_logs_html(logs)
                message = f"{user_name} 👋 - 📋 **Logs for Task #{task_id}**"
                html_message = self.markdown_to_html(message) + "\n\n" + formatted_logs
                await self.bot.send_message(room_id, message, html_message)
            else:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No logs available yet for task #{task_id}"
                )
        except Exception as e:
            logger.error(f"Failed to get logs for task {task_id}: {e}")
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Failed to retrieve logs for task #{task_id} ❌"
            )

    async def get_logs(self, room_id: str, args: list, sender: str | None):
        """Get logs for a task or control global log tailing.
        
        Supports:
        - !cd log - Get logs for last task (one-time)
        - !cd log <task_id> - Get logs for specific task (one-time)
        - !cd log on - Enable global log tailing (requires confirmation)
        - !cd log off - Disable global log tailing (requires confirmation)
        
        Args:
            room_id: Room to send response to
            args: Command arguments (on|off|task_id) - optional
            sender: User who requested the logs
        """
        # Check for log tailing control commands
        if args and args[0].lower() == 'on':
            await self._handle_log_tailing_on(room_id, sender)
            return
        
        if args and args[0].lower() == 'off':
            await self._handle_log_tailing_off(room_id, sender)
            return
        
        # Regular log retrieval
        await self._retrieve_task_logs(room_id, args, sender)

    async def tail_logs(self, room_id: str, task_id: int, project_id: int):
        """Tail logs for a running task and send incremental updates to the room.
        
        This implementation polls the Semaphore API asynchronously and sends
        only new log content as it becomes available, providing a near real-time
        streaming experience.
        
        Args:
            room_id: Room to send log updates to
            task_id: Task ID to tail
            project_id: Project ID
        """
        logger.info(f"Starting log tailing for task {task_id} in room {room_id}")
        last_log_size = 0
        poll_interval = 2  # Check every 2 seconds for more responsive tailing
        
        while room_id in self.log_tailing_sessions:
            # Check if this is still the right task
            if self.log_tailing_sessions[room_id]['task_id'] != task_id:
                logger.info(f"Log tailing for task {task_id} stopped - different task is being tailed")
                break
            
            try:
                # Get current task status
                task = await self.semaphore.get_task_status(project_id, task_id)
                if not task:
                    logger.warning(f"Could not get status for task {task_id}, retrying...")
                    await asyncio.sleep(poll_interval)
                    continue
                
                status = task.get('status')
                
                # Get current logs
                logs = await self.semaphore.get_task_output(project_id, task_id)
                
                # Check if there are new logs to send
                if logs and len(logs) > last_log_size:
                    # New logs available - extract only the new content
                    new_logs = logs[last_log_size:]
                    last_log_size = len(logs)
                    
                    # Send new log chunk asynchronously
                    is_final = status in ('success', 'error', 'stopped')
                    await self._send_log_chunk(room_id, task_id, new_logs, final=is_final)
                    
                    logger.debug(f"Sent {len(new_logs)} bytes of new logs for task {task_id}")
                
                # If task is finished, stop tailing
                if status in ('success', 'error', 'stopped'):
                    logger.info(f"Task {task_id} finished with status {status}, stopping log tailing")
                    
                    # Stop tailing
                    if room_id in self.log_tailing_sessions:
                        del self.log_tailing_sessions[room_id]
                    
                    # Send completion message
                    status_emoji = {
                        'success': '✅',
                        'error': '❌',
                        'stopped': '🛑'
                    }.get(status, '📋')
                    
                    message = f"{status_emoji} Log tailing completed for task **{task_id}** (status: **{status}**)"
                    html_message = self.markdown_to_html(message)
                    await self.bot.send_message(room_id, message, html_message)
                    break
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(f"Error tailing logs for task {task_id}: {e}", exc_info=True)
                # Wait longer on error before retrying
                await asyncio.sleep(poll_interval * 2)
        
        logger.info(f"Log tailing stopped for task {task_id} in room {room_id}")
    
    async def _send_log_chunk(self, room_id: str, task_id: int, log_chunk: str, final: bool = False):
        """Send a chunk of logs to the room with proper formatting.
        
        Sends incremental log updates as they become available, with proper
        HTML/markdown formatting for excellent rendering in Matrix clients.
        
        Args:
            room_id: Room to send to
            task_id: Task ID
            log_chunk: New log content (incremental update)
            final: Whether this is the final log chunk
        """
        # Skip empty chunks
        if not log_chunk or not log_chunk.strip():
            return
        
        # Format logs for plain text (strip ANSI codes)
        formatted_logs = self._format_task_logs(log_chunk)
        
        # Limit chunk size to avoid overwhelming messages
        # For tailing, we want smaller, more frequent updates
        max_lines = 30
        log_lines = formatted_logs.split('\n')
        
        if len(log_lines) > max_lines:
            # If chunk is too large, only show the last N lines
            formatted_logs = '\n'.join(log_lines[-max_lines:])
            truncated_chunk = '\n'.join(log_chunk.split('\n')[-max_lines:])
            header = f"📋 **Task {task_id}** (showing last {max_lines} of {len(log_lines)} total lines)\n\n"
        else:
            truncated_chunk = log_chunk
            if final:
                header = f"📋 **Task {task_id}** (FINAL)\n\n"
            else:
                header = f"📋 **Task {task_id}** (update)\n\n"
        
        # Create plain text version with markdown code block
        plain_message = f"{header}```\n{formatted_logs}\n```"
        
        # Create HTML version with proper color formatting and styling
        html_header = self.markdown_to_html(header)
        html_logs = self._format_task_logs_html(truncated_chunk)
        html_message = f"{html_header}{html_logs}"
        
        # Send the message asynchronously
        await self.bot.send_message(room_id, plain_message, html_message)

    def _ansi_to_html(self, text: str) -> str:
        """Convert ANSI color codes to Matrix-compatible HTML.
        
        This implementation converts ANSI codes to Matrix-supported HTML using
        data-mx-color attributes on <span> tags, which is the recommended approach
        per Matrix v1.10+ spec. Does NOT use inline style attributes which are
        stripped by Matrix clients for security.
        
        Handles combined codes like '\x1b[1;31m' (bold red) correctly.
        
        Args:
            text: Text with ANSI color codes
            
        Returns:
            Matrix-compatible HTML with proper color tags
        """
        # Escape HTML special characters first
        text = html.escape(text)
        
        # ANSI color code mappings to hex colors (using terminal color palette)
        # Note: '0' and '1' are handled separately in the logic
        ansi_colors = {
            '30': '#000000',  # black
            '31': '#cc0000',  # red
            '32': '#4e9a06',  # green
            '33': '#c4a000',  # yellow
            '34': '#3465a4',  # blue
            '35': '#75507b',  # magenta
            '36': '#06989a',  # cyan
            '37': '#d3d7cf',  # white
            '90': '#555753',  # bright-black
            '91': '#ef2929',  # bright-red
            '92': '#8ae234',  # bright-green
            '93': '#fce94f',  # bright-yellow
            '94': '#729fcf',  # bright-blue
            '95': '#ad7fa8',  # bright-magenta
            '96': '#34e2e2',  # bright-cyan
            '97': '#eeeeec',  # bright-white
        }
        
        # Stack to track open tags and their types
        open_tags = []  # List of tuples: (tag_type, tag_name)
        
        def replace_code(match):
            nonlocal open_tags
            codes = match.group(1).split(';') if match.group(1) else ['0']
            result = ''
            
            # Process all codes in the sequence (handles combined codes like '1;31' for bold red)
            for code in codes:
                code = code.strip()
                if code == '0' or code == '':
                    # Reset - close all open tags
                    while open_tags:
                        tag_type, _ = open_tags.pop()
                        if tag_type == 'bold':
                            result += '</strong>'
                        else:  # color
                            result += '</span>'
                elif code == '1':
                    # Bold - use <strong> tag (Matrix-supported)
                    result += '<strong>'
                    open_tags.append(('bold', 'bold'))
                elif code in ansi_colors:
                    # Color code - use <span> with data-mx-color (Matrix v1.10+ recommended)
                    color = ansi_colors[code]
                    result += f'<span data-mx-color="{color}">'
                    open_tags.append(('color', code))
            
            return result
        
        # Replace ANSI codes
        result = re.sub(r'\x1b\[([0-9;]*)m', replace_code, text)
        
        # Close any remaining open tags
        while open_tags:
            tag_type, _ = open_tags.pop()
            if tag_type == 'bold':
                result += '</strong>'
            else:  # color
                result += '</span>'
        
        return result

    def _ansi_to_html_for_pre(self, text: str) -> str:
        """Convert ANSI color codes to HTML for use in <pre> tags.
        
        This version does NOT replace newlines with <br> since <pre> tags
        preserve newlines naturally. Converts ANSI codes to proper HTML spans
        with color styling.
        
        Args:
            text: Text with ANSI color codes
            
        Returns:
            HTML formatted text (without <br> tags, preserves newlines)
        """
        # Use the improved ANSI to HTML conversion
        return self._ansi_to_html(text)

    def _format_task_logs(self, raw_logs: str) -> str:
        """Format raw task logs for better readability.
        
        Parses Ansible and Terraform output formats.
        
        Args:
            raw_logs: Raw log output
            
        Returns:
            Formatted log output
        """
        # Detect log type
        is_ansible = 'TASK [' in raw_logs or 'PLAY [' in raw_logs
        is_terraform = 'Terraform' in raw_logs or 'terraform' in raw_logs
        
        if is_ansible:
            # Clean up Ansible output
            # Remove ANSI color codes
            logs = re.sub(r'\x1b\[[0-9;]*m', '', raw_logs)
            # Remove excessive blank lines
            logs = re.sub(r'\n{3,}', '\n\n', logs)
            return logs.strip()
        elif is_terraform:
            # Clean up Terraform output
            logs = re.sub(r'\x1b\[[0-9;]*m', '', raw_logs)
            logs = re.sub(r'\n{3,}', '\n\n', logs)
            return logs.strip()
        else:
            # Generic formatting - just remove ANSI codes
            logs = re.sub(r'\x1b\[[0-9;]*m', '', raw_logs)
            return logs.strip()
    
    def _format_task_logs_html(self, raw_logs: str) -> str:
        """Format raw task logs with Matrix-compatible HTML formatting.
        
        Converts ANSI codes to Matrix-supported HTML using data-mx-color attributes
        instead of inline CSS styles. Uses <code> blocks for monospace rendering
        and <br/> for line breaks. This format is properly rendered by Element and
        other Matrix clients.
        
        Args:
            raw_logs: Raw log output with ANSI codes
            
        Returns:
            Matrix-compatible HTML formatted log output
        """
        # Remove excessive blank lines first
        logs = re.sub(r'\n{3,}', '\n\n', raw_logs)
        
        # Convert ANSI codes to Matrix-compatible HTML with data-mx-color attributes
        html_logs = self._ansi_to_html_for_pre(logs)
        
        # Split into lines and wrap each in <code> for monospace, separated by <br/>
        # This is the Matrix-compatible way to display multi-line code
        lines = html_logs.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():  # Non-empty line
                # Wrap in <code> for monospace rendering
                formatted_lines.append(f'<code>{line}</code>')
            else:
                # Empty line - just add a break
                formatted_lines.append('')
        
        # Join with <br/> tags for line breaks
        return '<br/>'.join(formatted_lines)

    async def ping_semaphore(self, room_id: str, sender: str | None):
        """Ping Semaphore server.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the ping
        """
        user_name = self._get_display_name(sender)
        success = await self.semaphore.ping()
        
        if success:
            plain_msg = self.message_manager.get_random_message('ping_success', user_name=user_name)
            # Add color to success message
            html_msg = self.markdown_to_html(plain_msg.replace('✅', self._color_success('✅')))
            await self.bot.send_message(
                room_id,
                plain_msg,
                html_msg,
                msgtype="m.notice"
            )
        else:
            plain_msg = f"{user_name} 👋 - ❌ Uh oh! Failed to ping Semaphore server 😟"
            # Add color to error message
            html_msg = self.markdown_to_html(plain_msg.replace('❌', self._color_error('❌')))
            await self.bot.send_message(
                room_id,
                plain_msg,
                html_msg,
                msgtype="m.notice"
            )

    def _gather_bot_system_info(self) -> tuple:
        """Gather bot and system information.
        
        Returns:
            Tuple of (text_lines, info_dict) where text_lines are for plain text
            and info_dict contains structured data for HTML tables
        """
        lines = []
        info_dict = {}
        
        # Basic bot info
        lines.append(f"• **Version:** {__version__}")
        lines.append(f"• **Platform:** {platform.system()} {platform.release()}")
        lines.append(f"• **Architecture:** {platform.machine()}")
        lines.append(f"• **Python:** {platform.python_version()}")
        
        info_dict['version'] = __version__
        info_dict['platform'] = f"{platform.system()} {platform.release()}"
        info_dict['architecture'] = platform.machine()
        info_dict['python'] = platform.python_version()
        
        # System resources
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            lines.append(f"• **CPU Usage:** {cpu_percent:.1f}%")
            lines.append(f"• **Memory Usage:** {memory.percent:.1f}% ({memory.used // (1024**2)} MB / {memory.total // (1024**2)} MB)")
            info_dict['cpu_percent'] = cpu_percent
            info_dict['memory'] = memory
        except Exception as e:
            logger.debug(f"Could not get system resources: {e}")
        
        # Network information (only if not redacting)
        redact_enabled = self.config.get('redact', False)
        if not redact_enabled:
            try:
                hostname = socket.gethostname()
                lines.append(f"• **Hostname:** {hostname}")
                info_dict['hostname'] = hostname
                
                # Get IP addresses
                ipv4_addrs = []
                ipv6_addrs = []
                try:
                    addrs = psutil.net_if_addrs()
                    for interface, addr_list in addrs.items():
                        for addr in addr_list:
                            if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                                ipv4_addrs.append(addr.address)
                            elif addr.family == socket.AF_INET6:
                                if not addr.address.startswith('::1') and not addr.address.startswith('fe80'):
                                    ipv6_addrs.append(addr.address.split('%')[0])
                    
                    if ipv4_addrs:
                        lines.append(f"• **IPv4:** {', '.join(ipv4_addrs)}")
                        info_dict['ipv4'] = ipv4_addrs
                    if ipv6_addrs:
                        lines.append(f"• **IPv6:** {', '.join(ipv6_addrs[:2])}")
                        info_dict['ipv6'] = ipv6_addrs[:2]
                except Exception as e:
                    logger.debug(f"Could not get IP addresses: {e}")
            except Exception as e:
                logger.debug(f"Could not get network info: {e}")
        
        return lines, info_dict

    def _gather_matrix_info(self) -> tuple:
        """Gather Matrix server information.
        
        Returns:
            Tuple of (text_lines, info_dict, connected, encrypted)
        """
        lines = []
        info_dict = {}
        connected = False
        encrypted = False
        
        if self.bot.client:
            lines.append(f"• **Homeserver:** {self.bot.client.homeserver}")
            lines.append(f"• **User ID:** {self.bot.client.user_id}")
            info_dict['homeserver'] = self.bot.client.homeserver
            info_dict['user_id'] = self.bot.client.user_id
            
            if hasattr(self.bot.client, 'device_id') and self.bot.client.device_id:
                lines.append(f"• **Device ID:** {self.bot.client.device_id}")
                info_dict['device_id'] = self.bot.client.device_id
            
            # Connection status
            if hasattr(self.bot.client, 'logged_in') and self.bot.client.logged_in:
                lines.append(f"• **Status:** Connected ✅")
                connected = True
            else:
                lines.append(f"• **Status:** Disconnected ❌")
            
            # Encryption status
            if hasattr(self.bot.client, 'olm') and self.bot.client.olm:
                lines.append(f"• **E2E Encryption:** Enabled 🔒")
                encrypted = True
            else:
                lines.append(f"• **E2E Encryption:** Disabled")
        
        return lines, info_dict, connected, encrypted

    def _build_info_html_tables(self, bot_info: dict, matrix_info: dict, 
                                matrix_connected: bool, matrix_encrypted: bool,
                                semaphore_info: dict) -> tuple:
        """Build HTML tables for info display.
        
        Returns:
            Tuple of (bot_table_html, matrix_table_html, semaphore_table_html)
        """
        redact_enabled = self.config.get('redact', False)
        
        # Bot info table
        bot_rows = [
            ['Version', bot_info['version']],
            ['Platform', bot_info['platform']],
            ['Architecture', bot_info['architecture']],
            ['Python', bot_info['python']],
        ]
        if 'cpu_percent' in bot_info:
            bot_rows.append(['CPU Usage', f"{bot_info['cpu_percent']:.1f}%"])
        if 'memory' in bot_info:
            mem = bot_info['memory']
            bot_rows.append(['Memory Usage', f"{mem.percent:.1f}% ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)"])
        if 'hostname' in bot_info and not redact_enabled:
            bot_rows.append(['Hostname', bot_info['hostname']])
        if 'ipv4' in bot_info and not redact_enabled:
            bot_rows.append(['IPv4', ', '.join(bot_info['ipv4'])])
        if 'ipv6' in bot_info and not redact_enabled:
            bot_rows.append(['IPv6', ', '.join(bot_info['ipv6'])])
        
        bot_table_html = '<table><thead><tr><th colspan="2">ChatrixCD Bot 🤖</th></tr></thead><tbody>'
        for key, value in bot_rows:
            bot_table_html += f'<tr><td><strong>{html.escape(key)}</strong></td><td>{html.escape(str(value))}</td></tr>'
        bot_table_html += '</tbody></table>'
        
        # Matrix info table
        matrix_table_html = '<table><thead><tr><th colspan="2">Matrix Server 🌐</th></tr></thead><tbody>'
        if matrix_info:
            for key in ['homeserver', 'user_id', 'device_id']:
                if key in matrix_info:
                    display_key = key.replace('_', ' ').title()
                    matrix_table_html += f'<tr><td><strong>{display_key}</strong></td><td>{html.escape(matrix_info[key])}</td></tr>'
            
            # Status with color
            if matrix_connected:
                matrix_table_html += f'<tr><td><strong>Status</strong></td><td>{self._color_success("Connected ✅")}</td></tr>'
            else:
                matrix_table_html += f'<tr><td><strong>Status</strong></td><td>{self._color_error("Disconnected ❌")}</td></tr>'
            
            # Encryption
            if matrix_encrypted:
                matrix_table_html += '<tr><td><strong>E2E Encryption</strong></td><td>Enabled 🔒</td></tr>'
            else:
                matrix_table_html += '<tr><td><strong>E2E Encryption</strong></td><td>Disabled</td></tr>'
        matrix_table_html += '</tbody></table>'
        
        # Semaphore info table
        semaphore_table_html = '<table><thead><tr><th colspan="2">Semaphore Server 🔧</th></tr></thead><tbody>'
        if semaphore_info:
            if 'version' in semaphore_info:
                semaphore_table_html += f'<tr><td><strong>Version</strong></td><td>{html.escape(str(semaphore_info.get("version")))}</td></tr>'
            for key, value in semaphore_info.items():
                if key != 'version':
                    semaphore_table_html += f'<tr><td><strong>{html.escape(key.replace("_", " ").title())}</strong></td><td>{html.escape(str(value))}</td></tr>'
        else:
            semaphore_table_html += f'<tr><td colspan="2">{self._color_error("Failed to get Semaphore info ❌")}</td></tr>'
        semaphore_table_html += '</tbody></table>'
        
        return bot_table_html, matrix_table_html, semaphore_table_html

    async def get_semaphore_info(self, room_id: str, sender: str | None):
        """Get Semaphore, Matrix server, and bot system info.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the info
        """
        user_name = self._get_display_name(sender)
        
        # Get Semaphore info
        semaphore_info = await self.semaphore.get_info()
        
        # Gather information
        bot_lines, bot_info = self._gather_bot_system_info()
        matrix_lines, matrix_info, matrix_connected, matrix_encrypted = self._gather_matrix_info()
        
        # Build plain text message
        message = f"{user_name} 👋 Here's the technical stuff! ℹ️\n\n"
        message += "**System Information**\n\n"
        message += "**ChatrixCD Bot** 🤖\n"
        message += "\n".join(bot_lines) + "\n\n"
        message += "**Matrix Server** 🌐\n"
        message += "\n".join(matrix_lines) + "\n\n"
        
        # Semaphore information
        if semaphore_info:
            message += "**Semaphore Server** 🔧\n"
            if 'version' in semaphore_info:
                message += f"• **Version:** {semaphore_info.get('version')}\n"
            for key, value in semaphore_info.items():
                if key != 'version':
                    message += f"• **{key.replace('_', ' ').title()}:** {value}\n"
        else:
            message += "**Semaphore Server** 🔧\n"
            message += "• Failed to get Semaphore info ❌\n"
        
        # Build HTML message
        greeting_html = self.markdown_to_html(user_name)
        bot_table_html, matrix_table_html, semaphore_table_html = self._build_info_html_tables(
            bot_info, matrix_info, matrix_connected, matrix_encrypted, semaphore_info
        )
        
        html_message = f"""{greeting_html} 👋 Here's the technical stuff! ℹ️<br/><br/>
<strong>System Information</strong><br/><br/>
{bot_table_html}<br/>
{matrix_table_html}<br/>
{semaphore_table_html}
"""
        
        await self.bot.send_message(room_id, message, html_message)

    async def list_command_aliases(self, room_id: str, sender: str | None):
        """List all command aliases.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        aliases = self.alias_manager.list_aliases()
        user_name = self._get_display_name(sender)
        
        if not aliases:
            plain_msg = f"{user_name} 👋 - No command aliases configured. 🔖"
            html_msg = self.markdown_to_html(plain_msg)
            await self.bot.send_message(
                room_id,
                plain_msg,
                html_msg,
                msgtype="m.notice"
            )
            return
        
        # Plain text version
        message = f"{user_name} 👋 Here are your command shortcuts! 🔖\n\n"
        message += "**Command Aliases**\n\n"
        for alias, command in aliases.items():
            message += f"• **{alias}** → `{command}`\n"
        
        # HTML version with table
        greeting_html = self.markdown_to_html(user_name)
        table_html = '<table><thead><tr><th>Alias</th><th>Command</th></tr></thead><tbody>'
        for alias, command in aliases.items():
            table_html += f'<tr><td><strong>{html.escape(alias)}</strong></td><td><code>{html.escape(command)}</code></td></tr>'
        table_html += '</tbody></table>'
        
        html_message = f"{greeting_html} 👋 Here are your command shortcuts! 🔖<br/><br/><strong>Command Aliases</strong><br/><br/>{table_html}"
        
        await self.bot.send_message(room_id, message, html_message, msgtype="m.notice")

    async def handle_pet(self, room_id: str, sender: str):
        """Handle the secret 'pet' command (positive reinforcement).
        
        Args:
            room_id: Room to send response to
            sender: User who petted the bot
        """
        user_name = self._get_display_name(sender)
        await self.bot.send_message(
            room_id,
            self.message_manager.get_random_message('pet', user_name=user_name)
            
        )

    async def handle_scold(self, room_id: str, sender: str):
        """Handle the secret 'scold' command (negative feedback).
        
        Args:
            room_id: Room to send response to
            sender: User who scolded the bot
        """
        user_name = self._get_display_name(sender)
        await self.bot.send_message(
            room_id,
            self.message_manager.get_random_message('scold', user_name=user_name)
            
        )
