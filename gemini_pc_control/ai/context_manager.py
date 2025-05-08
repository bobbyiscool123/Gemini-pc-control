"""Context management module for tracking conversation and system state."""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field

from loguru import logger

from gemini_pc_control.config import default_config
from gemini_pc_control.logging_config import log_performance


@dataclass
class CommandEntry:
    """Entry for a command in the conversation history."""
    
    timestamp: float
    command: str
    user_prompt: str
    result: str
    screenshot_id: str  # Reference to stored screenshot


@dataclass
class ContextWindow:
    """Rolling window of context entries."""
    
    max_entries: int = 10
    time_window: int = 3600  # 1 hour in seconds
    entries: List[CommandEntry] = field(default_factory=list)
    
    def add_entry(self, entry: CommandEntry) -> None:
        """Add a new entry to the context window."""
        self.entries.append(entry)
        self._prune_old_entries()
    
    def _prune_old_entries(self) -> None:
        """Remove entries that exceed the max count or are too old."""
        # Prune by count
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        # Prune by time
        cutoff_time = time.time() - self.time_window
        self.entries = [e for e in self.entries if e.timestamp >= cutoff_time]
    
    def get_recent_entries(self, count: Optional[int] = None) -> List[CommandEntry]:
        """Get the most recent entries."""
        if count is None:
            return self.entries
        return self.entries[-count:]
    
    def get_formatted_history(self) -> str:
        """Get a formatted string representation of the context history."""
        if not self.entries:
            return "No previous commands."
        
        result = "Previous commands:\n"
        for i, entry in enumerate(self.entries):
            dt = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            result += f"{i+1}. [{dt}] User: {entry.user_prompt}\n   System: {entry.command}\n"
        return result


class ContextManager:
    """Manage context for AI interactions."""
    
    def __init__(self, max_entries: int = 10, time_window: int = 3600):
        """Initialize the context manager."""
        self.conversation_context = ContextWindow(max_entries, time_window)
        self.system_state: Dict[str, Dict[str, Any]] = {}
        self.user_preferences: Dict[str, Any] = {}
        logger.debug("Initialized context manager")
    
    @log_performance
    def add_command(
        self, 
        user_prompt: str, 
        command: str, 
        result: str, 
        screenshot_id: str
    ) -> None:
        """Add a new command to the context history."""
        entry = CommandEntry(
            timestamp=time.time(),
            command=command,
            user_prompt=user_prompt,
            result=result,
            screenshot_id=screenshot_id
        )
        self.conversation_context.add_entry(entry)
        logger.debug(f"Added command to context: {user_prompt[:50]}...")
    
    def update_system_state(self, key: str, value: Any) -> None:
        """Update a system state value."""
        self.system_state[key] = {
            "value": value,
            "updated_at": time.time()
        }
        logger.debug(f"Updated system state: {key}={value}")
    
    def get_system_state(self, key: str) -> Optional[Any]:
        """Get a system state value if it exists and is not expired."""
        if key not in self.system_state:
            return None
        
        state_entry = self.system_state[key]
        # Check if entry is expired (1 hour)
        if time.time() - state_entry["updated_at"] > 3600:
            del self.system_state[key]
            logger.debug(f"System state expired: {key}")
            return None
        
        return state_entry["value"]
    
    def get_all_system_state(self, include_expired: bool = False) -> Dict[str, Any]:
        """Get all system state values, optionally including expired ones."""
        if include_expired:
            return {k: v["value"] for k, v in self.system_state.items()}
        
        # Filter out expired entries
        current_time = time.time()
        return {
            k: v["value"] 
            for k, v in self.system_state.items() 
            if current_time - v["updated_at"] <= 3600
        }
    
    def set_user_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        self.user_preferences[key] = value
        logger.debug(f"Set user preference: {key}={value}")
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.user_preferences.get(key, default)
    
    def get_context_for_prompt(self) -> Dict[str, Any]:
        """Get the context data formatted for inclusion in an AI prompt."""
        return {
            "conversation_history": [asdict(e) for e in self.conversation_context.get_recent_entries()],
            "system_state": self.get_all_system_state(),
            "user_preferences": self.user_preferences
        }
    
    @log_performance
    def save_to_disk(self, file_path: Optional[str] = None) -> bool:
        """Save the context to disk."""
        if file_path is None:
            file_path = os.path.join(default_config.app_dir, default_config.context_file)
        
        try:
            data = {
                "conversation_history": [asdict(e) for e in self.conversation_context.entries],
                "system_state": self.system_state,
                "user_preferences": self.user_preferences,
                "saved_at": time.time()
            }
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Context saved to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving context to {file_path}: {e}", exc_info=True)
            return False
    
    @log_performance
    def load_from_disk(self, file_path: Optional[str] = None) -> bool:
        """Load the context from disk."""
        if file_path is None:
            file_path = os.path.join(default_config.app_dir, default_config.context_file)
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Context file not found: {file_path}")
                return False
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Restore conversation history
            self.conversation_context.entries = [
                CommandEntry(**entry) for entry in data.get("conversation_history", [])
            ]
            
            # Restore system state and user preferences
            self.system_state = data.get("system_state", {})
            self.user_preferences = data.get("user_preferences", {})
            
            logger.info(f"Context loaded from {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading context from {file_path}: {e}", exc_info=True)
            return False
    
    def clear(self) -> None:
        """Clear all context data."""
        self.conversation_context.entries = []
        self.system_state = {}
        self.user_preferences = {}
        logger.info("Context cleared")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context."""
        return {
            "conversation_entries": len(self.conversation_context.entries),
            "system_state_keys": list(self.system_state.keys()),
            "user_preferences_keys": list(self.user_preferences.keys()),
            "total_context_size": len(str(self.get_context_for_prompt()))
        } 