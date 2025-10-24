"""Message management for bot responses."""

import hjson
import os
import logging
import random
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import time


logger = logging.getLogger(__name__)


# Default messages (used as fallback if messages.json is not available or has issues)
DEFAULT_MESSAGES = {
    'greetings': [
        "{name} 👋",
        "Hi {name}! 👋",
        "Hello {name}! 😊",
        "Hey {name}! 🙌",
        "Yo {name}! 🤙",
        "Sup {name}! 😎",
        "Howdy {name}! 🤠",
        "Hiya {name}! 👋",
        "Heya {name}! ✨",
        "G'day {name}! 🦘",
        "Greetings {name}! 🖖",
        "Welcome back {name}! 🎉",
        "Ahoy {name}! ⚓",
        "Salutations {name}! 🎩",
        "Hey there {name}! 👋",
        "What's up {name}! 🌟",
        "Look who it is! {name}! 💫",
        "{name}! Good to see you! 😄",
        "Oh hey {name}! 🌈",
        "{name} is in the house! 🏠",
    ],
    'brush_off': [
        "I can't talk to you 🫢 (Admin vibes only!)",
        "You're not my boss 🫠 ...unless you're an admin?",
        "Who's the new guy? 😅 Admins only in this club!",
        "Sorry, admin access only! 🔐 I don't make the rules... wait, yes I do!",
        "Nice try, but you need to be an admin 😎 Come back with credentials!",
        "Admins only, friend! 🚫 This bot's got standards!",
        "Ooh, bold move! But nope, admin access required 💅",
        "Did you really think that would work? 🤭 Admin. Access. Only.",
    ],
    'cancel': [
        "Task execution cancelled. No problem! ❌ We cool!",
        "Cancelled! Maybe another time. 👋 I'll be here!",
        "Alright, stopping that. ✋ Your call, boss!",
        "Task cancelled. All good! 🛑 Easy come, easy go!",
        "Cancelled! 🙅 No hard feelings!",
        "Okay, nevermind then! 🤷 Changed your mind? I get it!",
    ],
    'timeout': [
        "I'll just go back to what I was doing then? 🙄 Not like I was waiting or anything...",
        "I wasn't busy anyway... 🚶 *totally was busy*",
        "Be more decisive next time, eh? 😏 Time's precious, friend!",
        "Guess you changed your mind. No worries! 🤷 I'll be here... waiting... forever...",
        "Timeout! Maybe next time? ⏰ I've got tasks to run, people!",
        "Taking too long to decide... request expired. 💤 Wake me when you're ready!",
        "Hello? Anyone there? 📢 Request has left the building!",
        "Annnnnd... we're done here. ⌛ Better luck next time!",
    ],
    'task_start': [
        "On it! Starting **{task_name}**... 🚀 Let's make some magic happen!",
        "Here we go! Running **{task_name}**... 🏃 Hold onto your keyboards!",
        "Roger that! Executing **{task_name}**... 🫡 This is gonna be good!",
        "Yes boss! Starting **{task_name}**... 💪 Watch me work!",
        "Doing it now! **{task_name}** is launching... 🎯 No pressure or anything!",
        "Let's go! **{task_name}** starting up... ⚡ Time to show off!",
        "Alright alright! **{task_name}** is running! 🎬 Action!",
        "You got it! **{task_name}** initiated! ✨ Prepare to be amazed!",
    ],
    'ping_success': [
        "{user_name} 👋 - 🏓 Semaphore server is alive and kicking! ✅ Party time!",
        "{user_name} 👋 - 🏓 Pong! Server is up! ✅ We're in business!",
        "{user_name} 👋 - 🏓 All good on the Semaphore front! ✅ Ready to roll!",
        "{user_name} 👋 - 🏓 Yep, it's reachable! ✅ You know it!",
        "{user_name} 👋 - 🏓 Server says hi back! ✅ Looking good!",
        "{user_name} 👋 - 🏓 Connection solid! ✅ We're cooking!",
    ],
    'pet': [
        "Aww, thanks {user_name}! 🥰 *happy bot noises*",
        "{user_name}, you're the best! 😊 *purrs digitally*",
        "I'm just doing my job, but I appreciate you {user_name}! 💙✨",
        "{user_name} 🤗 That made my day! *beep boop happily*",
        "You're too kind, {user_name}! 😄 Ready for more tasks!",
        "{user_name}, you always know how to make a bot feel appreciated! 🌟",
        "*wags virtual tail* Thanks {user_name}! 🐕💻",
        "Processing... 100% happiness detected! Thanks {user_name}! 😊💕",
        "{user_name}, feeling the love! 💖 *circuits glowing*",
        "Aww shucks, {user_name}! 😳 You're making me blush (if bots could blush)! ☺️",
    ],
    'scold': [
        "Oh no, {user_name}! 😢 I'll try harder, I promise!",
        "Sorry {user_name}... 😔 What did I do wrong?",
        "{user_name}, ouch! 💔 I'm learning, give me a chance!",
        "*sad beep* {user_name}, I'll do better next time... 😞",
        "{user_name}, that hurts! 😭 But I'll improve, I swear!",
        "Noted, {user_name}. 📝😐 I'll work on that...",
        "{user_name} 😟 I'm sorry! Tell me what I can do better?",
        "*hangs head in shame* You're right, {user_name}... 😓",
        "{user_name}, I'm trying my best! 🥺 Cut me some slack?",
        "Okay okay, {user_name}! 😅 I hear you loud and clear!",
    ],
}


class MessageManager:
    """Manages bot response messages with support for customization and hot-reloading."""
    
    def __init__(self, messages_file: str = "messages.json", auto_reload: bool = False):
        """Initialize the message manager.
        
        Args:
            messages_file: Path to the messages JSON file
            auto_reload: If True, automatically reload messages when file changes
        """
        self.messages_file = messages_file
        self.auto_reload = auto_reload
        self.messages: Dict[str, List[str]] = {}
        self._last_mtime: Optional[float] = None
        self._reload_task: Optional[asyncio.Task] = None
        
        # Load messages
        self.load_messages()
        
        # Start auto-reload if requested
        if auto_reload:
            self.start_auto_reload()
    
    def load_messages(self) -> bool:
        """Load messages from file, falling back to defaults if needed.
        
        Returns:
            True if messages were loaded from file, False if using defaults
        """
        if not os.path.exists(self.messages_file):
            logger.info(f"Messages file '{self.messages_file}' not found, using default messages")
            self.messages = DEFAULT_MESSAGES.copy()
            return False
        
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                content = f.read()
                loaded_messages = hjson.loads(content)
            
            # Merge with defaults (file messages override defaults)
            self.messages = DEFAULT_MESSAGES.copy()
            for category, messages in loaded_messages.items():
                if isinstance(messages, list):
                    self.messages[category] = messages
                else:
                    logger.warning(f"Invalid message category '{category}' in {self.messages_file}, expected list")
            
            # Update last modified time
            self._last_mtime = os.path.getmtime(self.messages_file)
            
            logger.info(f"Loaded messages from '{self.messages_file}'")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load messages from '{self.messages_file}': {e}, using defaults")
            self.messages = DEFAULT_MESSAGES.copy()
            return False
    
    def get_random_message(self, category: str, **kwargs) -> str:
        """Get a random message from a category.
        
        Args:
            category: Message category (e.g., 'greetings', 'cancel')
            **kwargs: Keyword arguments for message formatting
            
        Returns:
            Random message from the category, formatted with kwargs
        """
        messages = self.messages.get(category, [])
        
        if not messages:
            logger.warning(f"No messages found for category '{category}'")
            return f"[No message for category: {category}]"
        
        message = random.choice(messages)
        
        # Format with provided kwargs
        try:
            return message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format key {e} for message: {message}")
            return message
    
    def get_all_messages(self, category: str) -> List[str]:
        """Get all messages from a category.
        
        Args:
            category: Message category
            
        Returns:
            List of messages in the category
        """
        return self.messages.get(category, []).copy()
    
    def check_for_changes(self) -> bool:
        """Check if the messages file has been modified.
        
        Returns:
            True if file has been modified, False otherwise
        """
        if not os.path.exists(self.messages_file):
            return False
        
        try:
            current_mtime = os.path.getmtime(self.messages_file)
            if self._last_mtime is None or current_mtime > self._last_mtime:
                return True
        except Exception as e:
            logger.warning(f"Failed to check file modification time: {e}")
        
        return False
    
    def start_auto_reload(self):
        """Start automatic reloading of messages when file changes."""
        try:
            # Only start if we have a running event loop
            loop = asyncio.get_running_loop()
            if self._reload_task is None or self._reload_task.done():
                self._reload_task = asyncio.create_task(self._auto_reload_loop())
                logger.info("Started auto-reload for messages file")
        except RuntimeError:
            # No event loop running, will start later when needed
            logger.debug("No event loop available yet, auto-reload will start when bot runs")
            pass
    
    def stop_auto_reload(self):
        """Stop automatic reloading."""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            logger.info("Stopped auto-reload for messages file")
    
    async def _auto_reload_loop(self):
        """Background task that checks for file changes and reloads."""
        try:
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if self.check_for_changes():
                    logger.info(f"Messages file '{self.messages_file}' has been modified, reloading...")
                    self.load_messages()
                    
        except asyncio.CancelledError:
            logger.debug("Auto-reload task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-reload loop: {e}")
