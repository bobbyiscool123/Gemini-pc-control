"""Response model for AI responses."""

from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field


class ResponseType(Enum):
    """Types of AI responses."""
    
    COMMAND = auto()  # A command to execute
    ERROR = auto()  # An error response
    INFORMATION = auto()  # Informational response
    FUNCTION_CALL = auto()  # Function call response (for structured commands)


class FunctionCall(BaseModel):
    """Function call for structured command execution."""
    
    name: str
    arguments: Dict[str, Any]


class AIResponse(BaseModel):
    """Model for AI response data."""
    
    id: str = Field(..., description="Unique identifier for the response")
    type: ResponseType
    created_at: datetime = Field(default_factory=datetime.now)
    prompt_id: str
    raw_text: str
    parsed_text: Optional[str] = None
    
    # For function calls
    function_calls: List[FunctionCall] = Field(default_factory=list)
    
    # Metadata
    model_name: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    
    # Additional context or metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error response."""
        return self.type == ResponseType.ERROR
    
    @property
    def is_command(self) -> bool:
        """Check if this is a command response."""
        return self.type == ResponseType.COMMAND
    
    @property
    def is_function_call(self) -> bool:
        """Check if this is a function call response."""
        return self.type == ResponseType.FUNCTION_CALL
    
    @property
    def has_function_calls(self) -> bool:
        """Check if this response has function calls."""
        return len(self.function_calls) > 0
    
    @classmethod
    def create_error_response(cls, prompt_id: str, error_message: str, model_name: str) -> "AIResponse":
        """Create an error response."""
        import uuid
        
        return cls(
            id=str(uuid.uuid4()),
            type=ResponseType.ERROR,
            prompt_id=prompt_id,
            raw_text=error_message,
            parsed_text=error_message,
            model_name=model_name,
        )
    
    @classmethod
    def create_information_response(cls, prompt_id: str, message: str, model_name: str) -> "AIResponse":
        """Create an informational response."""
        import uuid
        
        return cls(
            id=str(uuid.uuid4()),
            type=ResponseType.INFORMATION,
            prompt_id=prompt_id,
            raw_text=message,
            parsed_text=message,
            model_name=model_name,
        ) 