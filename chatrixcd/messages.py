"""Message management for bot responses."""

import hjson
import os
import logging
import random
from typing import Dict, List, Optional
from chatrixcd.file_watcher import FileWatcher

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
        "Roger! Executing **{task_name}**... 🫡 This is gonna be good!",
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
        self.messages: Dict[str, List[str]] = {}
        self._file_watcher: Optional[FileWatcher] = None
        
        self.load_messages()
        
        if auto_reload:
            self._file_watcher = FileWatcher(
                file_path=messages_file,
                reload_callback=lambda: self.load_messages(),
                auto_reload=True
            )
    
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
                loaded_messages = hjson.load(f)
            
            # Merge with defaults (file messages override defaults)
            self.messages = DEFAULT_MESSAGES.copy()
            for category, messages in loaded_messages.items():
                if isinstance(messages, list):
                    self.messages[category] = messages
                else:
                    logger.warning(f"Invalid message category '{category}' in {self.messages_file}, expected list")
            
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

