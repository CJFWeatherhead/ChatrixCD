"""Semaphore Webhook Plugin - Task monitoring via Gotify webhooks."""

import asyncio
import logging
import aiohttp
import json
from typing import Optional, Dict, Any
from chatrixcd.plugin_manager import TaskMonitorPlugin

logger = logging.getLogger(__name__)


class SemaphoreWebhookPlugin(TaskMonitorPlugin):
    """Plugin for monitoring Semaphore tasks via Gotify webhooks.
    
    This plugin receives push notifications from Gotify when Semaphore
    task status changes, providing instant notifications without polling.
    """
    
    def __init__(self, bot: Any, config: Dict[str, Any], metadata: Any):
        """Initialize the Semaphore Webhook plugin.
        
        Args:
            bot: Reference to ChatrixBot instance
            config: Plugin configuration
            metadata: Plugin metadata
        """
        super().__init__(bot, config, metadata)
        self.gotify_url = config.get('gotify_url')
        self.gotify_token = config.get('gotify_token')
        self.gotify_app_token = config.get('gotify_app_token')
        self.webhook_mode = config.get('webhook_mode', 'websocket')
        self.fallback_poll_interval = config.get('fallback_poll_interval', 60)
        
        # Track monitored tasks
        self.monitored_tasks: Dict[int, Dict[str, Any]] = {}
        
        # WebSocket connection
        self.ws_task: Optional[asyncio.Task] = None
        self.ws_session: Optional[aiohttp.ClientSession] = None
        self.ws_connected = False
        
        # Fallback polling task
        self.fallback_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.logger.info("Initializing Semaphore Webhook plugin")
        
        # Validate configuration
        if not self.gotify_url:
            self.logger.error("Gotify URL not configured")
            return False
        
        if not self.gotify_token:
            self.logger.error("Gotify token not configured")
            return False
        
        self.logger.info(f"Gotify URL: {self.gotify_url}, Mode: {self.webhook_mode}")
        return True
    
    async def start(self) -> bool:
        """Start the plugin."""
        self.logger.info("Starting Semaphore Webhook plugin")
        self.monitoring_active = True
        
        # Start WebSocket connection
        if self.webhook_mode == 'websocket':
            self.ws_task = asyncio.create_task(self._websocket_listener())
        
        # Start fallback polling task
        self.fallback_task = asyncio.create_task(self._fallback_polling())
        
        return True
    
    async def stop(self):
        """Stop the plugin."""
        self.logger.info("Stopping Semaphore Webhook plugin")
        self.monitoring_active = False
        
        # Stop WebSocket connection
        if self.ws_task and not self.ws_task.done():
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                # Expected when cancelling the WebSocket task; safe to ignore
                pass
        
        # Stop fallback polling
        if self.fallback_task and not self.fallback_task.done():
            self.fallback_task.cancel()
            try:
                await self.fallback_task
            except asyncio.CancelledError:
                # Expected when cancelling the fallback polling task; safe to ignore
                pass
        
        # Close WebSocket session
        if self.ws_session and not self.ws_session.closed:
            await self.ws_session.close()
        
        self.monitored_tasks.clear()
    
    async def cleanup(self):
        """Clean up resources."""
        await self.stop()
    
    async def monitor_task(self, project_id: int, task_id: int, room_id: str, task_name: Optional[str], sender: Optional[str] = None):
        """Monitor a Semaphore task via webhooks.
        
        Args:
            project_id: Semaphore project ID
            task_id: Task ID to monitor
            room_id: Matrix room ID for notifications
            task_name: Optional task name
            sender: Optional sender user ID for personalized notifications
        """
        if not self.monitoring_active:
            self.logger.warning("Monitoring not active, ignoring task monitor request")
            return
        
        # Store task info
        self.monitored_tasks[task_id] = {
            'project_id': project_id,
            'room_id': room_id,
            'task_name': task_name,
            'sender': sender,
            'last_status': None,
            'start_time': asyncio.get_event_loop().time()
        }
        
        self.logger.info(f"Started monitoring task {task_id} via webhooks")
        
        # Send initial status check to ensure we don't miss quick tasks
        await self._check_task_status(task_id)
    
    async def _websocket_listener(self):
        """Listen for Gotify messages via WebSocket."""
        self.logger.info("Starting Gotify WebSocket listener")
        
        # Build WebSocket URL with proper scheme replacement
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.gotify_url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        ws_url = urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        ws_url = f"{ws_url}/stream?token={self.gotify_token}"
        
        retry_delay = 5
        max_retry_delay = 300
        
        try:
            while self.monitoring_active:
                try:
                    # Create session if needed
                    if self.ws_session is None or self.ws_session.closed:
                        self.ws_session = aiohttp.ClientSession()
                    
                    # Connect to WebSocket
                    self.logger.info(f"Connecting to Gotify WebSocket: {self.gotify_url}")
                    async with self.ws_session.ws_connect(ws_url) as ws:
                        self.ws_connected = True
                        self.logger.info("Connected to Gotify WebSocket")
                        retry_delay = 5  # Reset retry delay on successful connection
                        
                        # Listen for messages
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_gotify_message(msg.data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
                        
                        self.ws_connected = False
                        self.logger.warning("Gotify WebSocket connection closed")
                        
                except asyncio.CancelledError:
                    self.logger.info("Gotify WebSocket listener cancelled")
                    raise
                except Exception as e:
                    self.ws_connected = False
                    self.logger.error(f"Gotify WebSocket error: {e}")
                    
                    # Exponential backoff for reconnection
                    self.logger.info(f"Retrying WebSocket connection in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
        finally:
            if self.ws_session is not None and not self.ws_session.closed:
                await self.ws_session.close()
    
    async def _handle_gotify_message(self, data: str):
        """Handle a message received from Gotify.
        
        Args:
            data: JSON message data
        """
        try:
            message = json.loads(data)
            
            # Extract Semaphore task information from message
            # This assumes Semaphore sends notifications in a specific format
            # Adjust parsing based on actual Semaphore notification structure
            title = message.get('title', '')
            content = message.get('message', '')
            
            # Parse task ID from title or content
            # Format: "Task #123 completed" or similar
            task_id = self._extract_task_id(title, content)
            if task_id is None:
                self.logger.debug(f"Could not extract task ID from message: {title}")
                return
            
            # Check if we're monitoring this task
            if task_id not in self.monitored_tasks:
                self.logger.debug(f"Received notification for unmonitored task {task_id}")
                return
            
            # Parse status from message
            status = self._extract_status(title, content)
            if status is None:
                self.logger.debug(f"Could not extract status from message: {title}")
                return
            
            # Process status update
            await self._process_status_update(task_id, status)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gotify message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling Gotify message: {e}", exc_info=True)
    
    def _extract_task_id(self, title: str, content: str) -> Optional[int]:
        """Extract task ID from Gotify message.
        
        Args:
            title: Message title
            content: Message content
            
        Returns:
            Task ID or None
        """
        import re
        
        # Try to find task ID in title or content
        for text in [title, content]:
            match = re.search(r'[Tt]ask\s*#?(\d+)', text)
            if match:
                return int(match.group(1))
            
            match = re.search(r'[Tt]ask[_ ]?[Ii][Dd]:?\s*(\d+)', text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_status(self, title: str, content: str) -> Optional[str]:
        """Extract task status from Gotify message.
        
        Args:
            title: Message title
            content: Message content
            
        Returns:
            Status string or None
        """
        # Common status keywords
        status_keywords = {
            'running': 'running',
            'started': 'running',
            'success': 'success',
            'completed': 'success',
            'finished': 'success',
            'failed': 'error',
            'error': 'error',
            'stopped': 'stopped',
            'cancelled': 'stopped',
        }
        
        # Check title and content for status keywords
        text = f"{title} {content}".lower()
        for keyword, status in status_keywords.items():
            if keyword in text:
                return status
        
        return None
    
    async def _process_status_update(self, task_id: int, status: str):
        """Process a task status update.
        
        Args:
            task_id: Task ID
            status: New status
        """
        task_info = self.monitored_tasks.get(task_id)
        if not task_info:
            return
        
        last_status = task_info['last_status']
        if status == last_status:
            return  # No change
        
        self.logger.info(f"Task {task_id} status update: {last_status} -> {status}")
        task_info['last_status'] = status
        
        # Send notification
        room_id = task_info['room_id']
        task_name = task_info['task_name']
        task_display = f"{task_name} ({task_id})" if task_name else str(task_id)
        
        if status == 'running':
            message = f"🔄 Task **{task_display}** is now running..."
            html_message = self._markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
            
        elif status == 'success':
            message = f"✅ Task **{task_display}** completed successfully!"
            html_message = self._markdown_to_html(message)
            event_id = await self.bot.send_message(room_id, message, html_message)
            if event_id:
                await self.bot.send_reaction(room_id, event_id, "🎉")
            
            # Clean up
            del self.monitored_tasks[task_id]
            
        elif status in ('error', 'stopped'):
            message = f"❌ Task **{task_display}** failed or was stopped (status: {status})"
            html_message = self._markdown_to_html(message)
            await self.bot.send_message(room_id, message, html_message)
            
            # Clean up
            del self.monitored_tasks[task_id]
    
    async def _fallback_polling(self):
        """Fallback polling for tasks when webhook connection is unavailable."""
        self.logger.info("Starting fallback polling task")
        
        while self.monitoring_active:
            await asyncio.sleep(self.fallback_poll_interval)
            
            # Only poll if WebSocket is not connected
            if not self.ws_connected and self.monitored_tasks:
                self.logger.debug(f"WebSocket disconnected, polling {len(self.monitored_tasks)} tasks")
                
                for task_id in list(self.monitored_tasks.keys()):
                    await self._check_task_status(task_id)
    
    async def _check_task_status(self, task_id: int):
        """Check task status via API (fallback).
        
        Args:
            task_id: Task ID
        """
        task_info = self.monitored_tasks.get(task_id)
        if not task_info:
            return
        
        try:
            project_id = task_info['project_id']
            semaphore = self.bot.semaphore
            task = await semaphore.get_task_status(project_id, task_id)
            
            if task:
                status = task.get('status')
                await self._process_status_update(task_id, status)
                
        except Exception as e:
            self.logger.error(f"Error checking task {task_id} status: {e}")
    
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
        status['monitored_tasks'] = len(self.monitored_tasks)
        status['websocket_connected'] = self.ws_connected
        status['webhook_mode'] = self.webhook_mode
        status['fallback_poll_interval'] = self.fallback_poll_interval
        return status
