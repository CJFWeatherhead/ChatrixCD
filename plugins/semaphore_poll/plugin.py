"""Semaphore Poll Plugin - Task monitoring via API polling."""

import asyncio
import logging
from typing import Optional, Dict, Any
from chatrixcd.plugin_manager import TaskMonitorPlugin

logger = logging.getLogger(__name__)


class SemaphorePollPlugin(TaskMonitorPlugin):
    """Plugin for monitoring Semaphore tasks via API polling.
    
    This plugin implements the traditional polling-based task monitoring
    that was previously built into the bot's command handler.
    """
    
    def __init__(self, bot: Any, config: Dict[str, Any], metadata: Any):
        """Initialize the Semaphore Poll plugin.
        
        Args:
            bot: Reference to ChatrixBot instance
            config: Plugin configuration
            metadata: Plugin metadata
        """
        super().__init__(bot, config, metadata)
        self.poll_interval = config.get('poll_interval', 10)
        self.notification_interval = config.get('notification_interval', 300)
        self.active_tasks: Dict[int, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}
        
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info("Initializing Semaphore Poll plugin")
        self.logger.info(f"Poll interval: {self.poll_interval}s, Notification interval: {self.notification_interval}s")
        return True
    
    async def start(self) -> bool:
        """Start the plugin."""
        self.logger.info("Starting Semaphore Poll plugin")
        self.monitoring_active = True
        return True
    
    async def stop(self):
        """Stop the plugin."""
        self.logger.info("Stopping Semaphore Poll plugin")
        self.monitoring_active = False
        
        # Cancel all monitoring tasks
        for task_id, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.monitoring_tasks.clear()
        self.active_tasks.clear()
    
    async def cleanup(self):
        """Clean up resources."""
        await self.stop()
    
    async def monitor_task(self, project_id: int, task_id: int, room_id: str, task_name: Optional[str]):
        """Monitor a Semaphore task via polling.
        
        Args:
            project_id: Semaphore project ID
            task_id: Task ID to monitor
            room_id: Matrix room ID for notifications
            task_name: Optional task name
        """
        if not self.monitoring_active:
            self.logger.warning("Monitoring not active, ignoring task monitor request")
            return
        
        # Store task info
        self.active_tasks[task_id] = {
            'project_id': project_id,
            'room_id': room_id,
            'task_name': task_name,
            'last_status': None,
            'last_notification_time': asyncio.get_event_loop().time()
        }
        
        # Create monitoring task
        monitor_task = asyncio.create_task(self._poll_task_status(task_id))
        self.monitoring_tasks[task_id] = monitor_task
        
        self.logger.info(f"Started monitoring task {task_id} (poll interval: {self.poll_interval}s)")
    
    async def _poll_task_status(self, task_id: int):
        """Poll task status and send notifications.
        
        Args:
            task_id: Task ID to monitor
        """
        task_info = self.active_tasks[task_id]
        project_id = task_info['project_id']
        room_id = task_info['room_id']
        task_name = task_info['task_name']
        
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        
        try:
            while task_id in self.active_tasks and self.monitoring_active:
                await asyncio.sleep(self.poll_interval)
                
                # Get task status from Semaphore
                semaphore = self.bot.semaphore
                task = await semaphore.get_task_status(project_id, task_id)
                
                if not task:
                    continue
                
                status = task.get('status')
                current_time = asyncio.get_event_loop().time()
                last_status = task_info['last_status']
                last_notification_time = task_info['last_notification_time']
                
                # Check for status change
                if status != last_status:
                    self.logger.info(f"Task {task_id} status changed: {last_status} -> {status}")
                    task_info['last_status'] = status
                    task_info['last_notification_time'] = current_time
                    
                    if status == 'running':
                        message = f"🔄 Task **{task_display}** is now running..."
                        html_message = self._markdown_to_html(message)
                        await self.bot.send_message(room_id, message, html_message)
                        
                        # Start log tailing if enabled
                        await self._maybe_start_log_tailing(task_id, project_id, room_id, task_display)
                        
                    elif status == 'success':
                        await self._send_completion_notification(room_id, task_id, task_display, '✅', 'completed successfully')
                        await self._cleanup_task(task_id)
                        break
                        
                    elif status in ('error', 'stopped'):
                        await self._send_completion_notification(room_id, task_id, task_display, '❌', f"failed or was stopped (status: {status})")
                        await self._cleanup_task(task_id)
                        break
                        
                # Send periodic "still running" notifications
                elif status == 'running' and (current_time - last_notification_time) >= self.notification_interval:
                    message = f"⏳ Task **{task_display}** is still running..."
                    html_message = self._markdown_to_html(message)
                    await self.bot.send_message(room_id, message, html_message)
                    task_info['last_notification_time'] = current_time
                    
        except asyncio.CancelledError:
            self.logger.info(f"Monitoring cancelled for task {task_id}")
            raise
        except Exception as e:
            self.logger.error(f"Error monitoring task {task_id}: {e}", exc_info=True)
            # Send error notification
            try:
                message = f"❌ Error monitoring task **{task_display}**: {str(e)}"
                html_message = self._markdown_to_html(message)
                await self.bot.send_message(room_id, message, html_message)
            except Exception:
                pass
        finally:
            await self._cleanup_task(task_id)
    
    async def _send_completion_notification(self, room_id: str, task_id: int, 
                                           task_display: str, emoji: str, status_text: str):
        """Send task completion notification.
        
        Args:
            room_id: Room ID
            task_id: Task ID
            task_display: Task display name
            emoji: Status emoji
            status_text: Status text
        """
        # Get the sender who started the task
        task_info = self.active_tasks.get(task_id, {})
        sender = task_info.get('sender')
        
        # Get display name from command handler
        if hasattr(self.bot, 'command_handler'):
            sender_name = self.bot.command_handler._get_display_name(sender) if sender else "there"
        else:
            sender_name = sender if sender else "there"
        
        message = f"{sender_name} 👋 Your task **{task_display}** {status_text}! {emoji}"
        html_message = self._markdown_to_html(message)
        event_id = await self.bot.send_message(room_id, message, html_message)
        
        # React with party emoji for success
        if emoji == '✅' and event_id:
            await self.bot.send_reaction(room_id, event_id, "🎉")
    
    async def _maybe_start_log_tailing(self, task_id: int, project_id: int, 
                                      room_id: str, task_display: str):
        """Start log tailing if global log tailing is enabled.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            room_id: Room ID
            task_display: Task display name
        """
        if not hasattr(self.bot, 'command_handler'):
            return
        
        cmd_handler = self.bot.command_handler
        
        # Check if global log tailing is enabled for this room
        if cmd_handler.global_log_tailing_enabled.get(room_id, False):
            if room_id not in cmd_handler.log_tailing_sessions:
                self.logger.info(f"Auto-starting log tailing for task {task_id}")
                cmd_handler.log_tailing_sessions[room_id] = {
                    'task_id': task_id,
                    'project_id': project_id,
                    'last_log_size': 0
                }
                
                log_message = f"📋 Starting log stream for task **{task_display}**..."
                await self.bot.send_message(room_id, log_message, self._markdown_to_html(log_message))
                
                # Start the tailing task
                asyncio.create_task(cmd_handler.tail_logs(room_id, task_id, project_id))
    
    async def _cleanup_task(self, task_id: int):
        """Clean up task monitoring.
        
        Args:
            task_id: Task ID
        """
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        if task_id in self.monitoring_tasks:
            del self.monitoring_tasks[task_id]
    
    def _markdown_to_html(self, text: str) -> str:
        """Convert simple markdown to HTML.
        
        Args:
            text: Markdown text
            
        Returns:
            HTML text
        """
        # Use the bot's command handler's markdown_to_html if available
        if hasattr(self.bot, 'command_handler'):
            return self.bot.command_handler.markdown_to_html(text)
        
        # Fallback: simple conversion
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status['active_tasks'] = len(self.active_tasks)
        status['poll_interval'] = self.poll_interval
        status['notification_interval'] = self.notification_interval
        return status
