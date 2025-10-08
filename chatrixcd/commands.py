"""Command handling for the bot."""

import logging
import asyncio
from typing import Dict, Any, Optional
from nio import MatrixRoom, RoomMessageText
from chatrixcd.semaphore import SemaphoreClient

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

    async def handle_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming message and process commands.
        
        Args:
            room: Room where message was sent
            event: Message event
        """
        message = event.body.strip()
        
        # Check if message starts with command prefix
        if not message.startswith(self.command_prefix):
            return
            
        # Check if room is allowed
        if not self.is_allowed_room(room.room_id):
            logger.info(f"Ignoring command in non-allowed room: {room.room_id}")
            return
            
        # Parse command
        parts = message[len(self.command_prefix):].strip().split()
        if not parts:
            await self.send_help(room.room_id)
            return
            
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
        elif command == 'logs':
            await self.get_logs(room.room_id, args)
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
        help_text = f"""**ChatrixCD Bot Commands**

{self.command_prefix} help - Show this help message
{self.command_prefix} projects - List available projects
{self.command_prefix} templates <project_id> - List templates for a project
{self.command_prefix} run <project_id> <template_id> - Run a task from template
{self.command_prefix} status <task_id> - Check status of a task
{self.command_prefix} stop <task_id> - Stop a running task
{self.command_prefix} logs <task_id> - Get logs for a task
"""
        await self.bot.send_message(room_id, help_text)

    async def list_projects(self, room_id: str):
        """List available Semaphore projects.
        
        Args:
            room_id: Room to send response to
        """
        projects = await self.semaphore.get_projects()
        
        if not projects:
            await self.bot.send_message(room_id, "No projects found or error accessing Semaphore.")
            return
            
        message = "**Available Projects:**\n\n"
        for project in projects:
            message += f"• **{project.get('name')}** (ID: {project.get('id')})\n"
            
        await self.bot.send_message(room_id, message)

    async def list_templates(self, room_id: str, args: list):
        """List templates for a project.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (project_id)
        """
        if not args:
            await self.bot.send_message(
                room_id,
                f"Usage: {self.command_prefix} templates <project_id>"
            )
            return
            
        try:
            project_id = int(args[0])
        except ValueError:
            await self.bot.send_message(room_id, "Invalid project ID")
            return
            
        templates = await self.semaphore.get_project_templates(project_id)
        
        if not templates:
            await self.bot.send_message(
                room_id,
                f"No templates found for project {project_id}"
            )
            return
            
        message = f"**Templates for Project {project_id}:**\n\n"
        for template in templates:
            message += f"• **{template.get('name')}** (ID: {template.get('id')})\n"
            if template.get('description'):
                message += f"  {template.get('description')}\n"
                
        await self.bot.send_message(room_id, message)

    async def run_task(self, room_id: str, sender: str, args: list):
        """Run a task from a template.
        
        Args:
            room_id: Room to send response to
            sender: User who sent the command
            args: Command arguments (project_id, template_id)
        """
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
            await self.bot.send_message(room_id, "Invalid project or template ID")
            return
            
        await self.bot.send_message(room_id, f"Starting task from template {template_id}...")
        
        task = await self.semaphore.start_task(project_id, template_id)
        
        if not task:
            await self.bot.send_message(room_id, "Failed to start task")
            return
            
        task_id = task.get('id')
        self.active_tasks[task_id] = {
            'project_id': project_id,
            'room_id': room_id,
            'sender': sender,
            'task': task
        }
        
        await self.bot.send_message(
            room_id,
            f"✅ Task {task_id} started successfully!\nUse '{self.command_prefix} status {task_id}' to check progress."
        )
        
        # Start monitoring the task
        asyncio.create_task(self.monitor_task(project_id, task_id, room_id))

    async def monitor_task(self, project_id: int, task_id: int, room_id: str):
        """Monitor a task and report status updates.
        
        Args:
            project_id: Project ID
            task_id: Task ID
            room_id: Room to send updates to
        """
        logger.info(f"Monitoring task {task_id}")
        last_status = None
        
        while task_id in self.active_tasks:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            task = await self.semaphore.get_task_status(project_id, task_id)
            if not task:
                continue
                
            status = task.get('status')
            
            if status != last_status:
                logger.info(f"Task {task_id} status changed: {last_status} -> {status}")
                last_status = status
                
                if status == 'running':
                    await self.bot.send_message(
                        room_id,
                        f"🔄 Task {task_id} is now running..."
                    )
                elif status == 'success':
                    await self.bot.send_message(
                        room_id,
                        f"✅ Task {task_id} completed successfully!"
                    )
                    del self.active_tasks[task_id]
                    break
                elif status in ('error', 'stopped'):
                    await self.bot.send_message(
                        room_id,
                        f"❌ Task {task_id} failed or was stopped. Status: {status}"
                    )
                    del self.active_tasks[task_id]
                    break

    async def check_status(self, room_id: str, args: list):
        """Check status of a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id)
        """
        if not args:
            await self.bot.send_message(
                room_id,
                f"Usage: {self.command_prefix} status <task_id>"
            )
            return
            
        try:
            task_id = int(args[0])
        except ValueError:
            await self.bot.send_message(room_id, "Invalid task ID")
            return
            
        if task_id not in self.active_tasks:
            await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks")
            return
            
        project_id = self.active_tasks[task_id]['project_id']
        task = await self.semaphore.get_task_status(project_id, task_id)
        
        if not task:
            await self.bot.send_message(room_id, f"Could not get status for task {task_id}")
            return
            
        status = task.get('status', 'unknown')
        message = f"**Task {task_id} Status:** {status}"
        
        if task.get('start'):
            message += f"\n**Started:** {task.get('start')}"
        if task.get('end'):
            message += f"\n**Ended:** {task.get('end')}"
            
        await self.bot.send_message(room_id, message)

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
            await self.bot.send_message(room_id, "Invalid task ID")
            return
            
        if task_id not in self.active_tasks:
            await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks")
            return
            
        project_id = self.active_tasks[task_id]['project_id']
        success = await self.semaphore.stop_task(project_id, task_id)
        
        if success:
            await self.bot.send_message(room_id, f"✅ Task {task_id} stopped")
            del self.active_tasks[task_id]
        else:
            await self.bot.send_message(room_id, f"❌ Failed to stop task {task_id}")

    async def get_logs(self, room_id: str, args: list):
        """Get logs for a task.
        
        Args:
            room_id: Room to send response to
            args: Command arguments (task_id)
        """
        if not args:
            await self.bot.send_message(
                room_id,
                f"Usage: {self.command_prefix} logs <task_id>"
            )
            return
            
        try:
            task_id = int(args[0])
        except ValueError:
            await self.bot.send_message(room_id, "Invalid task ID")
            return
            
        if task_id not in self.active_tasks:
            await self.bot.send_message(room_id, f"Task {task_id} not found in active tasks")
            return
            
        project_id = self.active_tasks[task_id]['project_id']
        logs = await self.semaphore.get_task_output(project_id, task_id)
        
        if logs:
            # Truncate logs if too long
            max_length = 4000
            if len(logs) > max_length:
                logs = logs[-max_length:] + "\n\n... (truncated)"
                
            await self.bot.send_message(
                room_id,
                f"**Logs for Task {task_id}:**\n```\n{logs}\n```"
            )
        else:
            await self.bot.send_message(room_id, f"No logs available for task {task_id}")
