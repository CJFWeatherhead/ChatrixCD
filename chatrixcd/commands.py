"""Command handling for the bot."""

import logging
import asyncio
import re
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
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user is admin or no restrictions, False otherwise
        """
        if not self.admin_users:
            return True
        return user_id in self.admin_users

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
        message += "Reply with **y**, **yes**, **go**, or **start** to confirm, or anything else to cancel."
        
        html_message = self.markdown_to_html(message)
        await self.bot.send_message(room_id, message, html_message)
        
        # Set timeout to clear confirmation after 60 seconds
        asyncio.create_task(self._clear_confirmation_timeout(confirmation_key, 60))

    async def _clear_confirmation_timeout(self, confirmation_key: str, timeout: int):
        """Clear a pending confirmation after timeout.
        
        Args:
            confirmation_key: The confirmation key
            timeout: Timeout in seconds
        """
        await asyncio.sleep(timeout)
        if confirmation_key in self.pending_confirmations:
            del self.pending_confirmations[confirmation_key]
            logger.info(f"Cleared confirmation timeout for {confirmation_key}")

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
        is_confirmed = message.strip().lower() in confirm_words
        
        if not is_confirmed:
            await self.bot.send_message(room_id, "Task execution cancelled. ❌")
            return
        
        # Execute the task
        project_id = confirmation['project_id']
        template_id = confirmation['template_id']
        template_name = confirmation['template_name']
        
        await self.bot.send_message(room_id, f"Starting task **{template_name}**... 🚀")
        
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
                    await self.bot.send_message(
                        room_id,
                        f"🔄 Task **{task_display}** is now running..."
                    )
                elif status == 'success':
                    await self.bot.send_message(
                        room_id,
                        f"✅ Task **{task_display}** completed successfully!"
                    )
                    del self.active_tasks[task_id]
                    break
                elif status in ('error', 'stopped'):
                    await self.bot.send_message(
                        room_id,
                        f"❌ Task **{task_display}** failed or was stopped. Status: {status}"
                    )
                    del self.active_tasks[task_id]
                    break
            elif status == 'running' and (current_time - last_notification_time) >= notification_interval:
                # Send periodic update for long-running tasks
                await self.bot.send_message(
                    room_id,
                    f"⏳ Task **{task_display}** is still running..."
                )
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
            await self.bot.send_message(room_id, f"🛑 Task **{task_display}** stopped")
            del self.active_tasks[task_id]
        else:
            await self.bot.send_message(room_id, f"❌ Failed to stop task **{task_display}**")

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
                
            if task_id not in self.active_tasks:
                await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks ❌")
                return
                
            project_id = self.active_tasks[task_id]['project_id']
        
        logs = await self.semaphore.get_task_output(project_id, task_id)
        
        if logs:
            task_name = self.active_tasks.get(task_id, {}).get('template_name')
            task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
            
            # Parse and format logs
            formatted_logs = self._format_task_logs(logs)
            
            # Tail only the last portion to avoid truncation
            max_lines = 100
            log_lines = formatted_logs.split('\n')
            if len(log_lines) > max_lines:
                formatted_logs = '\n'.join(log_lines[-max_lines:])
                header = f"**Logs for Task {task_display}** (last {max_lines} lines) 📋\n\n"
            else:
                header = f"**Logs for Task {task_display}** 📋\n\n"
            
            message = f"{header}```\n{formatted_logs}\n```"
            await self.bot.send_message(room_id, message)
        else:
            await self.bot.send_message(room_id, f"No logs available for task {task_id} ❌")

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
        """Get Semaphore server info.
        
        Args:
            room_id: Room to send response to
        """
        info = await self.semaphore.get_info()
        
        if info:
            message = "**Semaphore Server Info** ℹ️\n\n"
            
            # Display version info
            if 'version' in info:
                message += f"**Version:** {info.get('version')}\n"
            
            # Display any other relevant info
            for key, value in info.items():
                if key not in ['version']:
                    message += f"**{key.replace('_', ' ').title()}:** {value}\n"
            
            html_message = self.markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
        else:
            await self.bot.send_message(room_id, "❌ Failed to get Semaphore server info")

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
