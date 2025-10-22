"""Command handling for the bot."""

import logging
import asyncio
import re
import random
from typing import Dict, Any, Optional
from nio import MatrixRoom, RoomMessageText
from chatrixcd.semaphore import SemaphoreClient
from chatrixcd.aliases import AliasManager

logger = logging.getLogger(__name__)

# Greeting variations with emojis for personalized responses
GREETINGS = [
    "👋",  # Wave
    "Hi {name}! 👋"
    "Hello {name}! 😊"
    "Hey {name}! 🙌"
    "Yo {name}! 🤙"
    "Sup {name}! 😎"
    "Howdy {name}! 🤠"
    "Hiya {name}! 👋"
    "Heya {name}! ✨"
    "G'day {name}! 🦘"
    "Greetings {name}! 🖖"
    "Welcome {name}! 🎉"
    "Ahoy {name}! ⚓"
    "Salutations {name}! 🎩"
    "Hey there {name}! 👋"
    "What's up {name}! 🌟"
]


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
        
        # Initialize alias manager
        self.alias_manager = AliasManager()
        
        # Track pending confirmations for run commands
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        
        # Track message event IDs for threading reactions
        self.confirmation_message_ids: Dict[str, str] = {}
        
        # Track log tailing sessions: {room_id: {'task_id': int, 'project_id': int, 'last_log_size': int}}
        self.log_tailing_sessions: Dict[str, Dict[str, Any]] = {}

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

    def _get_display_name(self, user_id: str) -> str:
        """Get a friendly display name for a user.
        
        Args:
            user_id: User ID to get display name for
            
        Returns:
            Display name or username extracted from user ID
        """
        # Extract username from Matrix user ID (@username:server.com)
        if user_id.startswith('@'):
            username = user_id[1:].split(':')[0]
            return username
        return user_id
    
    def _get_greeting(self, user_id: str) -> str:
        """Get a random greeting for a user.
        
        Args:
            user_id: User ID to greet
            
        Returns:
            Random greeting with user's display name
        """
        name = self._get_display_name(user_id)
        greeting = random.choice(GREETINGS)
        return greeting.format(name=name)

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
        
        reaction_lower = reaction_key.lower()
        
        if reaction_key in positive_reactions or reaction_lower in positive_reactions:
            # Positive confirmation
            del self.pending_confirmations[confirmation_key]
            del self.confirmation_message_ids[confirmation_key]
            
            # Handle based on action type
            if confirmation.get('action') == 'exit':
                await self._execute_exit(room.room_id, sender)
            else:
                # Task execution
                await self._execute_task(room.room_id, confirmation)
                
        elif reaction_key in negative_reactions or reaction_lower in negative_reactions:
            # Negative confirmation
            del self.pending_confirmations[confirmation_key]
            del self.confirmation_message_ids[confirmation_key]
            
            cancel_responses = [
                "Task execution cancelled. No problem! ❌"
                "Cancelled! Maybe another time. 👋"
                "Alright, stopping that. ✋"
                "Task cancelled. All good! 🛑"
            ]
            await self.bot.send_message(
                room.room_id,
                random.choice(cancel_responses)
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
            brush_off_messages = [
                "I can't talk to you 🫢"
                "You're not my boss 🫠"
                "Who's the new guy? 😅"
                "Sorry, admin access only! 🔐"
                "Nice try, but you need to be an admin 😎"
                "Admins only, friend! 🚫"
            ]
            response = random.choice(brush_off_messages)
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

    async def send_help(self, room_id: str, sender: str = None):
        """Send help message.
        
        Args:
            room_id: Room to send help to
            sender: User who requested help (for personalization)
        """
        greeting = self._get_greeting(sender) if sender else "friend 👋"
        
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
        html_text = self.markdown_to_html(help_text)
        response_msg = f"Help requested by {sender}, sending response"
        logger.info(response_msg)
        await self.bot.send_message(room_id, help_text, html_text)

    async def list_admins(self, room_id: str, sender: str = None):
        """List admin users.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        greeting = self._get_greeting(sender) if sender else "friend 👋"
        if not self.admin_users:
            message = f"{greeting} Here's the admin roster! 👑\n\n"
            message += "**Admin Users**\n\n"
            message += "[dim]No admin users configured. All users have admin access.[/dim]"
        else:
            message = f"{greeting} Here are the bot overlords! 👑\n\n"
            message += "**Admin Users**\n\n"
            for admin in self.admin_users:
                message += f"• {admin}\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
    
    async def manage_rooms(self, room_id: str, args: list, sender: str = None):
        """Manage bot rooms (list, join, part).
        
        Args:
            room_id: Room to send response to
            args: Command arguments (action, optional room_id)
            sender: User who sent the command
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        
        if not args:
            # List rooms
            rooms = self.bot.client.rooms
            if not rooms:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Not currently in any rooms. 🏠"
                    
                )
                return
            
            message = f"{user_name} 👋 Here's where I hang out! 🏠\n\n"
            message += "**Rooms I'm In**\n\n"
            for room_id_key, room in rooms.items():
                room_name = room.display_name or "Unknown"
                message += f"• **{room_name}**\n  `{room_id_key}`\n"
            
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
            return
        
        action = args[0].lower()
        
        if action == 'join':
            if len(args) < 2:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} rooms join <room_id>"
                    
                )
                return
            
            target_room_id = args[1]
            try:
                await self.bot.client.join(target_room_id)
                await self.bot.send_message(
                    room_id,
                    f"✅ Joined room: {target_room_id}"
                    
                )
            except Exception as e:
                logger.error(f"Failed to join room {target_room_id}: {e}")
                await self.bot.send_message(
                    room_id,
                    f"❌ Failed to join room: {e}"
                    
                )
        
        elif action == 'part' or action == 'leave':
            if len(args) < 2:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Usage: {self.command_prefix} rooms part <room_id>"
                    
                )
                return
            
            target_room_id = args[1]
            try:
                await self.bot.client.room_leave(target_room_id)
                await self.bot.send_message(
                    room_id,
                    f"👋 Left room: {target_room_id}"
                    
                )
            except Exception as e:
                logger.error(f"Failed to leave room {target_room_id}: {e}")
                await self.bot.send_message(
                    room_id,
                    f"❌ Failed to leave room: {e}"
                    
                )
        
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
            
            message = f"{user_name} 👋 - ⚠️ **Confirm Bot Shutdown**\n\n"
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

    async def list_projects(self, room_id: str, sender: str = None):
        """List available Semaphore projects.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        projects = await self.semaphore.get_projects()
        user_name = self._get_display_name(sender) if sender else "friend"
        
        if not projects:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - No projects found or error accessing Semaphore. ❌"
                
            )
            return
        
        message = f"{user_name} 👋 Here's what we can work with! 📋\n\n"
        message += "**Available Projects:**\n\n"
        for project in projects:
            name = project.get('name')
            proj_id = project.get('id')
            message += f"• **{name}** (ID: {proj_id})\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

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

    async def list_templates(self, room_id: str, args: list, sender: str = None):
        """List templates for a project.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (project_id)
            sender: User who requested the list
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        
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
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - No templates found for project {project_id} ❌"
                
            )
            return
            
        message = f"{user_name} 👋 Here are the templates for project {project_id}! 📝\n\n"
        message += "**Templates:**\n\n"
        for template in templates:
            message += f"• **{template.get('name')}** (ID: {template.get('id')})\n"
            if template.get('description'):
                desc = self._format_description(template.get('description'))
                message += f"  {desc}\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def run_task(self, room_id: str, sender: str, args: list):
        """Run a task from a template.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
            args: Command arguments (project_id, template_id)
        """
        user_name = self._get_display_name(sender)
        
        # Smart parameter handling
        if len(args) == 0:
            # Try to auto-fill if only one project and one template
            projects = await self.semaphore.get_projects()
            if len(projects) == 1:
                project_id = projects[0].get('id')
                templates = await self.semaphore.get_project_templates(project_id)
                if len(templates) == 1:
                    template_id = templates[0].get('id')
                    logger.info(f"Auto-selected project {project_id} and template {template_id}")
                    args = [str(project_id), str(template_id)]
                else:
                    response = (f"{user_name} 👋 - Multiple templates available for project {project_id}.\n"
                        f"Use `{self.command_prefix} templates {project_id}` to list them.")
                    logger.info(f"Multiple templates found for auto-selection, sending: {response}")
                    await self.bot.send_message(room_id, response)
                    return
            else:
                response = (f"{user_name} 👋 - Usage: {self.command_prefix} run <project_id> <template_id>\n\n"
                    f"Use `{self.command_prefix} projects` to list available projects.")
                logger.info(f"No args provided for run command, sending: {response}")
                await self.bot.send_message(room_id, response)
                return
        elif len(args) == 1:
            # Only project_id provided, check if there's only one template
            try:
                project_id = int(args[0])
            except ValueError:
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Invalid project ID ❌"
                    
                )
                return
                
            templates = await self.semaphore.get_project_templates(project_id)
            if len(templates) == 1:
                template_id = templates[0].get('id')
                logger.info(f"Auto-selected template {template_id}")
                args.append(str(template_id))
            else:
                response = (f"{user_name} 👋 - Multiple templates available for project {project_id}.\n"
                    f"Use `{self.command_prefix} templates {project_id}` to list them.")
                logger.info(f"Multiple templates found for auto-selection, sending: {response}")
                await self.bot.send_message(room_id, response)
                return
        
        if len(args) < 2:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Usage: {self.command_prefix} run <project_id> <template_id>"
            )
            return
            
        try:
            project_id = int(args[0])
            template_id = int(args[1])
        except ValueError:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Invalid project or template ID ❌"
            )
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
        
        # Track the message ID for reaction handling
        if event_id:
            self.confirmation_message_ids[confirmation_key] = event_id
        
        # Set timeout to clear confirmation after 5 minutes
        asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 300, room_id))

    async def _clear_confirmation_timeout(self, confirmation_key: str, timeout: int, room_id: str = None):
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
                timeout_responses = [
                    "I'll just go back to what I was doing then? 🙄"
                    "I wasn't busy anyway... 🚶"
                    "Be more decisive next time, eh? 😏"
                    "Guess you changed your mind. No worries! 🤷"
                    "Timeout! Maybe next time? ⏰"
                    "Taking too long to decide... request expired. 💤"
                ]
                await self.bot.send_message(room_id, random.choice(timeout_responses))

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
        
        start_responses = [
            f"On it! Starting **{template_name}**... 🚀"
            f"Here we go! Running **{template_name}**... 🏃"
            f"Roger that! Executing **{template_name}**... 🫡"
            f"Yes boss! Starting **{template_name}**... 💪"
            f"Doing it now! **{template_name}** is launching... 🎯"
            f"Let's go! **{template_name}** starting up... ⚡"
        ]
        start_message = random.choice(start_responses)
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
            cancel_responses = [
                "Task execution cancelled. No problem! ❌"
                "Cancelled! Maybe another time. 👋"
                "Alright, stopping that. ✋"
                "Task cancelled. All good! 🛑"
            ]
            await self.bot.send_message(
                room_id,
                random.choice(cancel_responses)
                
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
        else:
            # Execute the task
            await self._execute_task(room_id, confirmation)

    async def monitor_task(self, project_id: int, task_id: int, room_id: str, task_name: str = None):
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

    async def check_status(self, room_id: str, args: list, sender: str = None):
        """Check status of a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id) - optional
            sender: User who requested the status
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        
        # If no args, use last task
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
        
        # Choose emoji based on status
        status_emoji = {
            'waiting': '⏸️',
            'running': '🔄',
            'success': '✅',
            'error': '❌',
            'stopped': '🛑',
            'unknown': '❓'
        }.get(status, '❓')
        
        message = f"{user_name} 👋 Here's the scoop! {status_emoji}\n\n"
        message += f"**Task {task_display} Status:** {status}\n\n"
        
        if task.get('start'):
            message += f"**Started:** {task.get('start')}\n"
        if task.get('end'):
            message += f"**Ended:** {task.get('end')}\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

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

    async def get_logs(self, room_id: str, args: list, sender: str = None):
        """Get logs for a task or control log tailing.
        
        Supports:
        - !cd log - Get logs for last task (one-time)
        - !cd log <task_id> - Get logs for specific task (one-time)
        - !cd log on - Start tailing logs for last task
        - !cd log off - Stop tailing logs
        
        Args:
            room_id: Room to send response to
            args: Command arguments (on|off|task_id) - optional
            sender: User who requested the logs
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        
        # Check if this is a log tailing control command
        if args and args[0].lower() == 'on':
            # Start log tailing for the last task
            if self.last_task_id is None:
                logger.info(f"Log tailing 'on' requested but no last task found")
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No task to tail logs for. Run a task first!"
                    
                )
                return
            
            # Start tailing
            self.log_tailing_sessions[room_id] = {
                'task_id': self.last_task_id,
                'project_id': self.last_project_id,
                'last_log_size': 0
            }
            
            logger.info(f"Started log tailing for task {self.last_task_id} in room {room_id}")
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Started tailing logs for task **{self.last_task_id}** 📋\n"
                f"Use `{self.command_prefix} log off` to stop."
                
            )
            
            # Start the tailing task
            asyncio.create_task(self.tail_logs(room_id, self.last_task_id, self.last_project_id))
            return
            
        elif args and args[0].lower() == 'off':
            # Stop log tailing
            if room_id not in self.log_tailing_sessions:
                logger.info(f"Log tailing 'off' requested but no active session in room {room_id}")
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - No active log tailing session."
                    
                )
                return
            
            task_id = self.log_tailing_sessions[room_id]['task_id']
            del self.log_tailing_sessions[room_id]
            
            logger.info(f"Stopped log tailing for task {task_id} in room {room_id}")
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - Stopped tailing logs for task **{task_id}** 🛑"
                
            )
            return
        
        # Regular log retrieval (one-time)
        # If no args, use last task
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
                
            # Check if task is in active tasks first
            if task_id in self.active_tasks:
                project_id = self.active_tasks[task_id]['project_id']
            # If not in active tasks but we have a last_project_id, try that
            elif self.last_task_id == task_id and self.last_project_id is not None:
                project_id = self.last_project_id
            else:
                # Try to get the project_id from semaphore if task exists
                # For now, just inform the user to provide project info
                logger.info(f"Task {task_id} not found in active tasks")
                await self.bot.send_message(
                    room_id,
                    f"{user_name} 👋 - Task {task_id} not found in active tasks.\n"
                    f"For finished tasks, use the last task with: `{self.command_prefix} log`"
                    
                )
                return
        
        logger.info(f"Fetching logs for task {task_id}")
        logs = await self.semaphore.get_task_output(project_id, task_id)
        
        if logs:
            task_name = self.active_tasks.get(task_id, {}).get('template_name')
            task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
            
            # Parse and format logs for plain text
            formatted_logs = self._format_task_logs(logs)
            
            # Tail only the last portion to avoid truncation
            max_lines = 100
            log_lines = formatted_logs.split('\n')
            if len(log_lines) > max_lines:
                formatted_logs = '\n'.join(log_lines[-max_lines:])
                header = f"{user_name} 👋 Here are the logs! (last {max_lines} lines) 📋\n\n"
                header += f"**Logs for Task {task_display}**\n\n"
            else:
                header = f"{user_name} 👋 Here are the logs! 📋\n\n"
                header += f"**Logs for Task {task_display}**\n\n"
            
            # Create plain text version with markdown code block
            plain_message = f"{header}```\n{formatted_logs}\n```"
            
            # Create HTML version with color formatting
            html_header = self.markdown_to_html(header)
            html_logs = self._format_task_logs_html(logs)
            
            # Tail HTML logs too if needed
            if len(log_lines) > max_lines:
                # Re-process with HTML formatting for tailed version
                tailed_raw_logs = '\n'.join(logs.split('\n')[-max_lines:])
                html_logs = self._format_task_logs_html(tailed_raw_logs)
            
            html_message = f"{html_header}{html_logs}"
            
            logger.info(f"Sending logs for task {task_id} ({len(log_lines)} lines, {len(logs)} bytes)")
            await self.bot.send_message(room_id, plain_message, html_message)
        else:
            logger.info(f"No logs available for task {task_id}")
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - No logs available for task {task_id} ❌"
                
            )

    async def tail_logs(self, room_id: str, task_id: int, project_id: int):
        """Tail logs for a running task and send updates to the room.
        
        Args:
            room_id: Room to send log updates to
            task_id: Task ID to tail
            project_id: Project ID
        """
        logger.info(f"Starting log tailing task for task {task_id} in room {room_id}")
        last_log_size = 0
        
        while room_id in self.log_tailing_sessions:
            # Check if this is still the right task
            if self.log_tailing_sessions[room_id]['task_id'] != task_id:
                logger.info(f"Log tailing task {task_id} stopped - different task is being tailed")
                break
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
            try:
                # Get current task status
                task = await self.semaphore.get_task_status(project_id, task_id)
                if not task:
                    logger.warning(f"Could not get status for task {task_id}, continuing...")
                    continue
                
                status = task.get('status')
                
                # If task is finished, send final logs and stop
                if status in ('success', 'error', 'stopped'):
                    logger.info(f"Task {task_id} finished with status {status}, sending final logs")
                    
                    # Get final logs
                    logs = await self.semaphore.get_task_output(project_id, task_id)
                    if logs and len(logs) > last_log_size:
                        new_logs = logs[last_log_size:]
                        await self._send_log_chunk(room_id, task_id, new_logs, final=True)
                    
                    # Stop tailing
                    if room_id in self.log_tailing_sessions:
                        del self.log_tailing_sessions[room_id]
                    
                    await self.bot.send_message(
                        room_id,
                        f"📋 Log tailing stopped for task **{task_id}** (status: {status})"
                    )
                    break
                
                # Get current logs
                logs = await self.semaphore.get_task_output(project_id, task_id)
                
                if logs and len(logs) > last_log_size:
                    # New logs available
                    new_logs = logs[last_log_size:]
                    last_log_size = len(logs)
                    
                    # Send new log chunk
                    await self._send_log_chunk(room_id, task_id, new_logs)
                    
            except Exception as e:
                logger.error(f"Error tailing logs for task {task_id}: {e}")
                await asyncio.sleep(10)  # Wait longer on error
        
        logger.info(f"Log tailing task stopped for task {task_id} in room {room_id}")
    
    async def _send_log_chunk(self, room_id: str, task_id: int, log_chunk: str, final: bool = False):
        """Send a chunk of logs to the room.
        
        Args:
            room_id: Room to send to
            task_id: Task ID
            log_chunk: New log content
            final: Whether this is the final log chunk
        """
        # Format logs
        formatted_logs = self._format_task_logs(log_chunk)
        
        # Limit chunk size to avoid huge messages
        max_lines = 50
        log_lines = formatted_logs.split('\n')
        if len(log_lines) > max_lines:
            formatted_logs = '\n'.join(log_lines[-max_lines:])
            header = f"📋 **Task {task_id}** (last {max_lines} lines)\n\n"
        else:
            header = f"📋 **Task {task_id}**\n\n"
        
        if final:
            header = f"📋 **Task {task_id}** (FINAL)\n\n"
        
        # Create plain text version with markdown code block
        plain_message = f"{header}```\n{formatted_logs}\n```"
        
        # Create HTML version with color formatting
        html_header = self.markdown_to_html(header)
        html_logs = self._format_task_logs_html(log_chunk if len(log_lines) <= max_lines else '\n'.join(log_chunk.split('\n')[-max_lines:]))
        html_message = f"{html_header}{html_logs}"
        
        await self.bot.send_message(room_id, plain_message, html_message)

    def _ansi_to_html(self, text: str) -> str:
        """Convert ANSI color codes to HTML.
        
        Args:
            text: Text with ANSI color codes
            
        Returns:
            HTML formatted text
        """
        # ANSI color code to HTML color mapping
        ansi_colors = {
            '30': 'black',
            '31': 'red',
            '32': 'green',
            '33': 'yellow',
            '34': 'blue',
            '35': 'magenta',
            '36': 'cyan',
            '37': 'white',
            '90': 'gray',
            '91': 'lightred',
            '92': 'lightgreen',
            '93': 'lightyellow',
            '94': 'lightblue',
            '95': 'lightmagenta',
            '96': 'lightcyan',
            '97': 'white'
        }
        
        # Convert color codes
        result = text
        
        # Handle bold (1m)
        result = re.sub(r'\x1b\[1m', '<strong>', result)
        
        # Handle color codes (e.g., 31m for red)
        for code, color in ansi_colors.items():
            result = re.sub(rf'\x1b\[{code}m', f'<span style="color: {color}">', result)
        
        # Handle reset codes (0m)
        result = re.sub(r'\x1b\[0m', '</span></strong>', result)
        
        # Clean up any remaining ANSI codes
        result = re.sub(r'\x1b\[[0-9;]*m', '', result)
        
        # Replace newlines with <br> for HTML
        result = result.replace('\n', '<br>')
        
        return result

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
        """Format raw task logs with HTML formatting, preserving colors.
        
        Args:
            raw_logs: Raw log output with ANSI codes
            
        Returns:
            HTML formatted log output
        """
        # Detect log type
        is_ansible = 'TASK [' in raw_logs or 'PLAY [' in raw_logs
        is_terraform = 'Terraform' in raw_logs or 'terraform' in raw_logs
        
        # Remove excessive blank lines first
        logs = re.sub(r'\n{3,}', '\n\n', raw_logs)
        
        # Convert ANSI codes to HTML
        html_logs = self._ansi_to_html(logs)
        
        # Wrap in pre tag for monospace formatting
        return f'<pre>{html_logs}</pre>'

    async def ping_semaphore(self, room_id: str, sender: str = None):
        """Ping Semaphore server.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the ping
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        success = await self.semaphore.ping()
        
        if success:
            ping_responses = [
                f"{user_name} 👋 - 🏓 Semaphore server is alive and kicking! ✅"
                f"{user_name} 👋 - 🏓 Pong! Server is up! ✅"
                f"{user_name} 👋 - 🏓 All good on the Semaphore front! ✅"
                f"{user_name} 👋 - 🏓 Yep, it's reachable! ✅"
            ]
            await self.bot.send_message(
                room_id,
                random.choice(ping_responses)
                
            )
        else:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - ❌ Uh oh! Failed to ping Semaphore server 😟"
                
            )

    async def get_semaphore_info(self, room_id: str, sender: str = None):
        """Get Semaphore and Matrix server info.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the info
        """
        user_name = self._get_display_name(sender) if sender else "friend"
        
        # Get Semaphore info
        semaphore_info = await self.semaphore.get_info()
        
        message = f"{user_name} 👋 Here's the technical stuff! ℹ️\n\n"
        message += "**Server Information**\n\n"
        
        # Matrix information
        message += "**Matrix Server** 🌐\n"
        if self.bot.client:
            message += f"• **Homeserver:** {self.bot.client.homeserver}\n"
            message += f"• **User ID:** {self.bot.client.user_id}\n"
            if hasattr(self.bot.client, 'device_id') and self.bot.client.device_id:
                message += f"• **Device ID:** {self.bot.client.device_id}\n"
            
            # Connection status
            if hasattr(self.bot.client, 'logged_in') and self.bot.client.logged_in:
                message += f"• **Status:** Connected ✅\n"
            else:
                message += f"• **Status:** Disconnected ❌\n"
            
            # Encryption status
            if hasattr(self.bot.client, 'olm') and self.bot.client.olm:
                message += f"• **E2E Encryption:** Enabled 🔒\n"
            else:
                message += f"• **E2E Encryption:** Disabled\n"
        
        message += "\n"
        
        # Semaphore information
        if semaphore_info:
            message += "**Semaphore Server** 🔧\n"
            
            # Display version info
            if 'version' in semaphore_info:
                message += f"• **Version:** {semaphore_info.get('version')}\n"
            
            # Display any other relevant info
            for key, value in semaphore_info.items():
                if key not in ['version']:
                    message += f"• **{key.replace('_', ' ').title()}:** {value}\n"
        else:
            message += "**Semaphore Server** 🔧\n"
            message += "• Failed to get Semaphore info ❌\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def list_command_aliases(self, room_id: str, sender: str = None):
        """List all command aliases.
        
        Args:
            room_id: Room to send response to
            sender: User who requested the list
        """
        aliases = self.alias_manager.list_aliases()
        user_name = self._get_display_name(sender) if sender else "friend"
        
        if not aliases:
            await self.bot.send_message(
                room_id,
                f"{user_name} 👋 - No command aliases configured. 🔖"
                
            )
            return
        
        message = f"{user_name} 👋 Here are your command shortcuts! 🔖\n\n"
        message += "**Command Aliases**\n\n"
        for alias, command in aliases.items():
            message += f"• **{alias}** → `{command}`\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def handle_pet(self, room_id: str, sender: str):
        """Handle the secret 'pet' command (positive reinforcement).
        
        Args:
            room_id: Room to send response to
            sender: User who petted the bot
        """
        user_name = self._get_display_name(sender)
        pet_responses = [
            f"Aww, thanks {user_name}! 🥰 *happy bot noises*"
            f"{user_name}, you're the best! 😊 *purrs digitally*"
            f"I'm just doing my job, but I appreciate you {user_name}! 💙✨"
            f"{user_name} 🤗 That made my day! *beep boop happily*"
            f"You're too kind, {user_name}! 😄 Ready for more tasks!"
            f"{user_name}, you always know how to make a bot feel appreciated! 🌟"
            f"*wags virtual tail* Thanks {user_name}! 🐕💻"
            f"Processing... 100% happiness detected! Thanks {user_name}! 😊💕"
            f"{user_name}, feeling the love! 💖 *circuits glowing*"
            f"Aww shucks, {user_name}! 😳 You're making me blush (if bots could blush)! ☺️"
        ]
        await self.bot.send_message(
            room_id,
            random.choice(pet_responses)
            
        )

    async def handle_scold(self, room_id: str, sender: str):
        """Handle the secret 'scold' command (negative feedback).
        
        Args:
            room_id: Room to send response to
            sender: User who scolded the bot
        """
        user_name = self._get_display_name(sender)
        scold_responses = [
            f"Oh no, {user_name}! 😢 I'll try harder, I promise!"
            f"Sorry {user_name}... 😔 What did I do wrong?"
            f"{user_name}, ouch! 💔 I'm learning, give me a chance!"
            f"*sad beep* {user_name}, I'll do better next time... 😞"
            f"{user_name}, that hurts! 😭 But I'll improve, I swear!"
            f"Noted, {user_name}. 📝😐 I'll work on that..."
            f"{user_name} 😟 I'm sorry! Tell me what I can do better?"
            f"*hangs head in shame* You're right, {user_name}... 😓"
            f"{user_name}, I'm trying my best! 🥺 Cut me some slack?"
            f"Okay okay, {user_name}! 😅 I hear you loud and clear!"
        ]
        await self.bot.send_message(
            room_id,
            random.choice(scold_responses)
            
        )
