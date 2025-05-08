"""Command model for representing system commands."""

from enum import Enum, auto
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from pydantic import BaseModel, Field


class CommandType(Enum):
    """Types of commands supported by the application."""
    
    MOUSE_MOVE = auto()
    MOUSE_CLICK = auto()
    KEYBOARD_TYPE = auto()
    KEYBOARD_HOTKEY = auto()
    START_PROCESS = auto()
    PRINT_OUTPUT = auto()
    COMPOSITE = auto()
    UNKNOWN = auto()


class CommandStatus(Enum):
    """Status of command execution."""
    
    PENDING = auto()
    EXECUTING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELED = auto()


class MouseMoveCommand(BaseModel):
    """Mouse movement command."""
    
    x: int
    y: int
    duration: float = 0.1


class MouseClickCommand(BaseModel):
    """Mouse click command."""
    
    button: str = "left"  # "left", "right", "middle"
    clicks: int = 1  # For double-click, etc.


class KeyboardTypeCommand(BaseModel):
    """Keyboard typing command."""
    
    text: str


class KeyboardHotkeyCommand(BaseModel):
    """Keyboard hotkey command."""
    
    keys: List[str]


class StartProcessCommand(BaseModel):
    """Start process command."""
    
    command: str


class PrintOutputCommand(BaseModel):
    """Print output command."""
    
    text: str


class Command(BaseModel):
    """Command model for representing system commands."""
    
    id: str = Field(..., description="Unique identifier for the command")
    type: CommandType
    status: CommandStatus = CommandStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_prompt: str
    raw_response: str
    error_message: Optional[str] = None
    screenshot_id: Optional[str] = None
    
    # Command-specific data
    data: Dict[str, Any] = Field(default_factory=dict)
    
    # For composite commands
    sub_commands: List["Command"] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True
    
    @property
    def is_composite(self) -> bool:
        """Check if this is a composite command."""
        return self.type == CommandType.COMPOSITE
    
    @property
    def duration(self) -> Optional[float]:
        """Get the execution duration in seconds, if available."""
        if self.completed_at and self.executed_at:
            return (self.completed_at - self.executed_at).total_seconds()
        return None
    
    def update_status(self, status: CommandStatus, error: Optional[str] = None) -> None:
        """Update the command status and related fields."""
        self.status = status
        
        if status == CommandStatus.EXECUTING and not self.executed_at:
            self.executed_at = datetime.now()
        
        if status == CommandStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()
        
        if status == CommandStatus.FAILED:
            self.error_message = error 