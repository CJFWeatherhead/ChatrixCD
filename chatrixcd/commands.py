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
            await self.handle_confirmation(room.room_id, event.sender, message)
            return
        
        # Check if message starts with command prefix
        if not message.startswith(self.command_prefix):
            return
            
        # Check if room is allowed
        if not self.is_allowed_room(room.room_id):
            logger.info(f"Ignoring command in non-allowed room: {room.room_id}")
            return
        
        # Check if user is admin (if admins are configured)
        if not self.is_admin(event.sender):
            # Send fun brush-off message
            brush_off_messages = [
                "I can't talk to you 🫢",
                "You're not my boss 🫠",
                "Who's the new guy? 😅",
                "Sorry, admin access only! 🔐",
                "Nice try, but you need to be an admin 😎",
                "Admins only, friend! 🚫"
            ]
            await self.bot.send_message(room.room_id, random.choice(brush_off_messages))
            return
            
        # Parse command
        command_text = message[len(self.command_prefix):].strip()
        if not command_text:
            await self.send_help(room.room_id)
            return
        
        # Resolve aliases
        resolved_command = self.alias_manager.resolve_command(command_text)
        parts = resolved_command.split()
        
        command = parts[0].lower()
        args = parts[1:]
        
        # Route to appropriate handler
        if command == 'help':
            await self.send_help(room.room_id)
        elif command == 'admins':
            await self.list_admins(room.room_id)
        elif command == 'rooms':
            await self.manage_rooms(room.room_id, args)
        elif command == 'exit':
            await self.exit_bot(room.room_id, event.sender)
        elif command == 'projects':
            await self.list_projects(room.room_id)
        elif command == 'templates':
            await self.list_templates(room.room_id, args)
        elif command == 'run':
            await self.run_task(room.room_id, event.sender, args)
        elif command == 'status':
            await self.check_status(room.room_id, args)
        elif command == 'stop':
            await self.stop_task(room.room_id, event.sender, args)
        elif command in ('logs', 'log'):
            await self.get_logs(room.room_id, args)
        elif command == 'ping':
            await self.ping_semaphore(room.room_id)
        elif command == 'info':
            await self.get_semaphore_info(room.room_id)
        elif command == 'aliases':
            await self.list_command_aliases(room.room_id)
        else:
            await self.bot.send_message(
                room.room_id,
                f"Unknown command: {command}. Type '{self.command_prefix} help' for available commands."
            )

    async def send_help(self, room_id: str):
        """Send help message.
        
        Args:
            room_id: Room to send help to
        """
        help_text = f"""**ChatrixCD Bot Commands** 📚

{self.command_prefix} help - Show this help message
{self.command_prefix} admins - List admin users
{self.command_prefix} rooms [join|part <room_id>] - List or manage rooms
{self.command_prefix} exit - Exit the bot (requires confirmation)
{self.command_prefix} projects - List available projects
{self.command_prefix} templates <project_id> - List templates for a project
{self.command_prefix} run <project_id> <template_id> - Run a task from template
{self.command_prefix} status [task_id] - Check status of a task (uses last task if no ID)
{self.command_prefix} stop <task_id> - Stop a running task
{self.command_prefix} logs [task_id] - Get logs for a task (uses last task if no ID)
{self.command_prefix} ping - Ping Semaphore server
{self.command_prefix} info - Get Semaphore server info
{self.command_prefix} aliases - List command aliases
"""
        html_text = self.markdown_to_html(help_text)
        await self.bot.send_message(room_id, help_text, html_text)

    async def list_admins(self, room_id: str):
        """List admin users.
        
        Args:
            room_id: Room to send response to
        """
        if not self.admin_users:
            message = "**Admin Users** 👑\n\n"
            message += "[dim]No admin users configured. All users have admin access.[/dim]"
        else:
            message = "**Admin Users** 👑\n\n"
            for admin in self.admin_users:
                message += f"• {admin}\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
    
    async def manage_rooms(self, room_id: str, args: list):
        """Manage bot rooms (list, join, part).
        
        Args:
            room_id: Room to send response to
            args: Command arguments (action, optional room_id)
        """
        if not args:
            # List rooms
            rooms = self.bot.client.rooms
            if not rooms:
                await self.bot.send_message(room_id, "Not currently in any rooms. 🏠")
                return
            
            message = "**Rooms I'm In** 🏠\n\n"
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
                    f"Usage: {self.command_prefix} rooms join <room_id>"
                )
                return
            
            target_room_id = args[1]
            try:
                await self.bot.client.join(target_room_id)
                await self.bot.send_message(room_id, f"✅ Joined room: {target_room_id}")
            except Exception as e:
                logger.error(f"Failed to join room {target_room_id}: {e}")
                await self.bot.send_message(room_id, f"❌ Failed to join room: {e}")
        
        elif action == 'part' or action == 'leave':
            if len(args) < 2:
                await self.bot.send_message(
                    room_id,
                    f"Usage: {self.command_prefix} rooms part <room_id>"
                )
                return
            
            target_room_id = args[1]
            try:
                await self.bot.client.room_leave(target_room_id)
                await self.bot.send_message(room_id, f"👋 Left room: {target_room_id}")
            except Exception as e:
                logger.error(f"Failed to leave room {target_room_id}: {e}")
                await self.bot.send_message(room_id, f"❌ Failed to leave room: {e}")
        
        else:
            await self.bot.send_message(
                room_id,
                f"Unknown action: {action}. Use 'join' or 'part'."
            )
    
    async def exit_bot(self, room_id: str, sender: str):
        """Exit the bot with confirmation.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
        """
        # Create a special confirmation for exit
        confirmation_key = f"{room_id}:{sender}:exit"
        
        # Check if already waiting for confirmation
        if confirmation_key in self.pending_confirmations:
            # User is confirming
            del self.pending_confirmations[confirmation_key]
            
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
        else:
            # Request confirmation
            self.pending_confirmations[confirmation_key] = {
                'action': 'exit',
                'room_id': room_id,
                'sender': sender,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            await self.bot.send_message(
                room_id,
                f"⚠️ **Confirm Bot Shutdown**\n\n"
                f"Are you sure you want to shut down the bot?\n\n"
                f"Reply with `{self.command_prefix} exit` again to confirm."
            )
            
            # Set timeout to clear confirmation after 30 seconds
            asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 30))

    async def list_projects(self, room_id: str):
        """List available Semaphore projects.
        
        Args:
            room_id: Room to send response to
        """
        projects = await self.semaphore.get_projects()
        
        if not projects:
            await self.bot.send_message(room_id, "No projects found or error accessing Semaphore. ❌")
            return
        
        message = "**Available Projects:** 📋\n\n"
        for project in projects:
            message += f"• **{project.get('name')}** (ID: {project.get('id')})\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def list_templates(self, room_id: str, args: list):
        """List templates for a project.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (project_id)
        """
        # If no args, try to get the only project if there's only one
        if not args:
            projects = await self.semaphore.get_projects()
            if len(projects) == 1:
                project_id = projects[0].get('id')
                logger.info(f"Auto-selecting only available project: {project_id}")
            else:
                await self.bot.send_message(
                    room_id,
                    f"Usage: {self.command_prefix} templates <project_id>\n\n"
                    f"Use `{self.command_prefix} projects` to list available projects."
                )
                return
        else:
            try:
                project_id = int(args[0])
            except ValueError:
                await self.bot.send_message(room_id, "Invalid project ID ❌")
                return
            
        templates = await self.semaphore.get_project_templates(project_id)
        
        if not templates:
            await self.bot.send_message(
                room_id,
                f"No templates found for project {project_id} ❌"
            )
            return
            
        message = f"**Templates for Project {project_id}:** 📝\n\n"
        for template in templates:
            message += f"• **{template.get('name')}** (ID: {template.get('id')})\n"
            if template.get('description'):
                message += f"  {template.get('description')}\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def run_task(self, room_id: str, sender: str, args: list):
        """Run a task from a template.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
            args: Command arguments (project_id, template_id)
        """
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
                    await self.bot.send_message(
                        room_id,
                        f"Multiple templates available for project {project_id}.\n"
                        f"Use `{self.command_prefix} templates {project_id}` to list them."
                    )
                    return
            else:
                await self.bot.send_message(
                    room_id,
                    f"Usage: {self.command_prefix} run <project_id> <template_id>\n\n"
                    f"Use `{self.command_prefix} projects` to list available projects."
                )
                return
        elif len(args) == 1:
            # Only project_id provided, check if there's only one template
            try:
                project_id = int(args[0])
            except ValueError:
                await self.bot.send_message(room_id, "Invalid project ID ❌")
                return
                
            templates = await self.semaphore.get_project_templates(project_id)
            if len(templates) == 1:
                template_id = templates[0].get('id')
                logger.info(f"Auto-selected template {template_id}")
                args.append(str(template_id))
            else:
                await self.bot.send_message(
                    room_id,
                    f"Multiple templates available for project {project_id}.\n"
                    f"Use `{self.command_prefix} templates {project_id}` to list them."
                )
                return
        
        if len(args) < 2:
            await self.bot.send_message(
                room_id,
                f"Usage: {self.command_prefix} run <project_id> <template_id>"
            )
            return
            
        try:
            project_id = int(args[0])
            template_id = int(args[1])
        except ValueError:
            await self.bot.send_message(room_id, "Invalid project or template ID ❌")
            return
        
        # Fetch template details for confirmation
        templates = await self.semaphore.get_project_templates(project_id)
        template = next((t for t in templates if t.get('id') == template_id), None)
        
        if not template:
            await self.bot.send_message(room_id, f"Template {template_id} not found in project {project_id} ❌")
            return
        
        template_name = template.get('name', f'Template {template_id}')
        template_desc = template.get('description', 'No description')
        
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
        
        message = f"**Confirm Task Execution** ⚠️\n\n"
        message += f"**Template:** {template_name}\n"
        message += f"**Description:** {template_desc}\n"
        message += f"**Project ID:** {project_id}\n"
        message += f"**Template ID:** {template_id}\n\n"
        message += "Reply with **y**, **yes**, **go**, or **start** to confirm.\n"
        message += "Reply with **n**, **no**, **cancel**, or **stop** to cancel."
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
        
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
                    "I'll just go back to what I was doing then? 🙄",
                    "I wasn't busy anyway... 🚶",
                    "Be more decisive next time, eh? 😏",
                    "Guess you changed your mind. No worries! 🤷",
                    "Timeout! Maybe next time? ⏰",
                    "Taking too long to decide... request expired. 💤"
                ]
                await self.bot.send_message(room_id, random.choice(timeout_responses))

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
        
        # Check if message is a confirmation
        confirm_words = ['y', 'yes', 'go', 'start', 'ok', '👍', '✓', '✅']
        cancel_words = ['n', 'no', 'cancel', 'stop', 'end', 'nope', '👎', '❌', '✖']
        
        message_lower = message.strip().lower()
        is_confirmed = message_lower in confirm_words
        is_cancelled = message_lower in cancel_words
        
        if is_cancelled:
            cancel_responses = [
                "Task execution cancelled. No problem! ❌",
                "Cancelled! Maybe another time. 👋",
                "Alright, stopping that. ✋",
                "Task cancelled. All good! 🛑"
            ]
            await self.bot.send_message(room_id, random.choice(cancel_responses))
            return
        
        if not is_confirmed:
            await self.bot.send_message(room_id, "Task execution cancelled. ❌")
            return
        
        # Execute the task with fun confirmation response
        project_id = confirmation['project_id']
        template_id = confirmation['template_id']
        template_name = confirmation['template_name']
        
        start_responses = [
            f"On it! Starting **{template_name}**... 🚀",
            f"Here we go! Running **{template_name}**... 🏃",
            f"Roger that! Executing **{template_name}**... 🫡",
            f"Yes boss! Starting **{template_name}**... 💪",
            f"Doing it now! **{template_name}** is launching... 🎯",
            f"Let's go! **{template_name}** starting up... ⚡"
        ]
        start_message = random.choice(start_responses)
        html_start_message = self.markdown_to_html(start_message)
        await self.bot.send_message(room_id, start_message, html_start_message)
        
        task = await self.semaphore.start_task(project_id, template_id)
        
        if not task:
            await self.bot.send_message(room_id, "Failed to start task ❌")
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
        await self.bot.send_message(room_id, message_text, html_message)
        
        # Start monitoring the task
        asyncio.create_task(self.monitor_task(project_id, task_id, room_id, template_name))

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
                    message = f"✅ Task **{task_display}** completed successfully!"
                    html_message = self.markdown_to_html(message)
                    event_id = await self.bot.send_message(room_id, message, html_message)
                    # React with party emoji
                    if event_id:
                        await self.bot.send_reaction(room_id, event_id, "🎉")
                    del self.active_tasks[task_id]
                    break
                elif status in ('error', 'stopped'):
                    message = f"❌ Task **{task_display}** failed or was stopped. Status: {status}"
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

    async def check_status(self, room_id: str, args: list):
        """Check status of a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id) - optional
        """
        # If no args, use last task
        if not args:
            if self.last_task_id is None:
                await self.bot.send_message(
                    room_id,
                    f"No task ID provided and no previous task found.\n"
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
                await self.bot.send_message(room_id, "Invalid task ID ❌")
                return
                
            if task_id not in self.active_tasks:
                await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks ❌")
                return
                
            project_id = self.active_tasks[task_id]['project_id']
        
        task = await self.semaphore.get_task_status(project_id, task_id)
        
        if not task:
            await self.bot.send_message(room_id, f"Could not get status for task {task_id} ❌")
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
        
        message = f"{status_emoji} **Task {task_display} Status:** {status}\n\n"
        
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
        if not args:
            await self.bot.send_message(
                room_id,
                f"Usage: {self.command_prefix} stop <task_id>"
            )
            return
            
        try:
            task_id = int(args[0])
        except ValueError:
            await self.bot.send_message(room_id, "Invalid task ID ❌")
            return
            
        if task_id not in self.active_tasks:
            await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks ❌")
            return
            
        project_id = self.active_tasks[task_id]['project_id']
        task_name = self.active_tasks[task_id].get('template_name')
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        
        success = await self.semaphore.stop_task(project_id, task_id)
        
        if success:
            message = f"🛑 Task **{task_display}** stopped"
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
            del self.active_tasks[task_id]
        else:
            message = f"❌ Failed to stop task **{task_display}**"
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)

    async def get_logs(self, room_id: str, args: list):
        """Get logs for a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id) - optional
        """
        # If no args, use last task
        if not args:
            if self.last_task_id is None:
                await self.bot.send_message(
                    room_id,
                    f"No task ID provided and no previous task found.\n"
                    f"Usage: {self.command_prefix} logs <task_id>"
                )
                return
            task_id = self.last_task_id
            project_id = self.last_project_id
            logger.info(f"Using last task ID: {task_id}")
        else:
            try:
                task_id = int(args[0])
            except ValueError:
                await self.bot.send_message(room_id, "Invalid task ID ❌")
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
                await self.bot.send_message(
                    room_id, 
                    f"Task {task_id} not found in active tasks.\n"
                    f"For finished tasks, use the last task with: `{self.command_prefix} logs`"
                )
                return
        
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
                header = f"**Logs for Task {task_display}** (last {max_lines} lines) 📋\n\n"
            else:
                header = f"**Logs for Task {task_display}** 📋\n\n"
            
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
            
            await self.bot.send_message(room_id, plain_message, html_message)
        else:
            await self.bot.send_message(room_id, f"No logs available for task {task_id} ❌")

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
            '97': 'white',
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

    async def ping_semaphore(self, room_id: str):
        """Ping Semaphore server.
        
        Args:
            room_id: Room to send response to
        """
        success = await self.semaphore.ping()
        
        if success:
            await self.bot.send_message(room_id, "🏓 Semaphore server is reachable! ✅")
        else:
            await self.bot.send_message(room_id, "❌ Failed to ping Semaphore server")

    async def get_semaphore_info(self, room_id: str):
        """Get Semaphore and Matrix server info.
        
        Args:
            room_id: Room to send response to
        """
        # Get Semaphore info
        semaphore_info = await self.semaphore.get_info()
        
        message = "**Server Information** ℹ️\n\n"
        
        # Matrix information
        message += "**Matrix Server**\n"
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
            message += "**Semaphore Server**\n"
            
            # Display version info
            if 'version' in semaphore_info:
                message += f"• **Version:** {semaphore_info.get('version')}\n"
            
            # Display any other relevant info
            for key, value in semaphore_info.items():
                if key not in ['version']:
                    message += f"• **{key.replace('_', ' ').title()}:** {value}\n"
        else:
            message += "**Semaphore Server**\n"
            message += "• Failed to get Semaphore info ❌\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)

    async def list_command_aliases(self, room_id: str):
        """List all command aliases.
        
        Args:
            room_id: Room to send response to
        """
        aliases = self.alias_manager.list_aliases()
        
        if not aliases:
            await self.bot.send_message(room_id, "No command aliases configured. 🔖")
            return
        
        message = "**Command Aliases** 🔖\n\n"
        for alias, command in aliases.items():
            message += f"• **{alias}** → `{command}`\n"
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
