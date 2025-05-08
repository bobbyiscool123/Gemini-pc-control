"""Gemini API client module."""

import base64
import os
import time
import uuid
from typing import Dict, List, Optional, Any, Union

import google.generativeai as genai
from loguru import logger

from gemini_pc_control.config import default_config
from gemini_pc_control.logging_config import log_performance
from gemini_pc_control.models.response import AIResponse, ResponseType, FunctionCall


class GeminiClient:
    """Client for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        self.api_key = self._get_gemini_api_key()
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=default_config.gemini.model_name,
            generation_config={
                "temperature": default_config.gemini.temperature,
                "max_output_tokens": default_config.gemini.max_output_tokens,
                "top_p": default_config.gemini.top_p,
                "top_k": default_config.gemini.top_k,
            }
        )
        logger.info(f"Initialized Gemini client with model {default_config.gemini.model_name}")
    
    def _get_gemini_api_key(self) -> str:
        """Get the Gemini API key from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Look for credentials file
            credentials_path = os.path.join(default_config.app_dir, default_config.credentials_file)
            if os.path.exists(credentials_path):
                from dotenv import load_dotenv
                load_dotenv(credentials_path)
                api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Please ensure you have set the GEMINI_API_KEY environment variable "
                "or created a .env file with your API key.\n"
                "You can get a Google Gemini API key from: https://aistudio.google.com/app/apikey"
            )
        
        return api_key
    
    @log_performance
    def generate_command(
        self, 
        user_prompt: str, 
        image_base64: str, 
        context_data: Optional[Dict[str, Any]] = None,
        retry: bool = False
    ) -> AIResponse:
        """Generate a command based on user prompt and visual context."""
        prompt_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            structured_prompt = self._create_structured_prompt(user_prompt, retry, context_data)
            function_declarations = self._get_function_declarations()
            
            # Create content parts
            contents = [structured_prompt]
            if image_base64:
                contents.append({
                    "mime_type": "image/png",
                    "data": image_base64
                })
            
            # Make API call with optional function calling
            generation_config = {
                "temperature": 0.2 if not retry else 0.4,  # Slightly higher temp on retry
                "max_output_tokens": default_config.gemini.max_output_tokens,
            }
            
            response = self.model.generate_content(
                contents=contents,
                generation_config=generation_config,
                tools=function_declarations
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Parse response
            result = AIResponse(
                id=prompt_id,
                type=ResponseType.COMMAND,
                prompt_id=prompt_id,
                raw_text=response.text.strip() if hasattr(response, 'text') else "",
                model_name=default_config.gemini.model_name,
                latency_ms=latency_ms,
                metadata={"retry": retry},
            )
            
            # Check for function calls
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_call = part.function_call
                                result.function_calls.append(
                                    FunctionCall(
                                        name=function_call.name,
                                        arguments=function_call.args
                                    )
                                )
                                result.type = ResponseType.FUNCTION_CALL
            
            # Add token usage if available
            if hasattr(response, 'usage'):
                result.prompt_tokens = response.usage.prompt_tokens
                result.completion_tokens = response.usage.completion_tokens
                result.total_tokens = response.usage.total_tokens
            
            logger.info(f"Generated command in {latency_ms:.2f}ms", 
                        prompt_id=prompt_id, 
                        model=default_config.gemini.model_name,
                        retry=retry)
            
            return result
        
        except Exception as e:
            error_msg = f"Error generating command: {str(e)}"
            logger.error(error_msg, prompt_id=prompt_id, exc_info=True)
            
            return AIResponse.create_error_response(
                prompt_id=prompt_id,
                error_message=error_msg,
                model_name=default_config.gemini.model_name
            )
    
    def _create_structured_prompt(
        self, 
        user_prompt: str, 
        retry: bool = False,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a structured prompt for the Gemini API."""
        # Example conversation history from context
        conversation_history = ""
        if context_data and "conversation_history" in context_data:
            for entry in context_data["conversation_history"][-3:]:  # Last 3 entries
                conversation_history += f"User: {entry.get('user_prompt', '')}\nSystem: {entry.get('command', '')}\n"
        
        # System state from context
        system_state = ""
        if context_data and "system_state" in context_data:
            for key, value in context_data["system_state"].items():
                system_state += f"{key}: {value}\n"
        
        return {
            "system": "You are a system command translator for Windows 10 x64. Your goal is to translate natural language into executable commands.",
            "context": {
                "os": "Windows 10 x64",
                "screen_context": "Base64 encoded screenshot provided for visual context",
                "available_commands": [
                    "pyautogui.moveTo", "pyautogui.click", "pyautogui.typewrite", 
                    "pyautogui.hotkey", "start"
                ],
                "execution_environment": "Python 3.13.1",
                "conversation_history": conversation_history,
                "system_state": system_state,
                "retry_attempt": retry
            },
            "examples": [
                {
                    "user_input": "Click on the save button",
                    "command_output": "pyautogui.moveTo(50, 100, duration=0.1); pyautogui.click()"
                },
                {
                    "user_input": "Open Chrome",
                    "command_output": "start \"C:/Program Files/Google/Chrome/Application/chrome.exe\""
                },
                {
                    "user_input": "Open Discord",
                    "command_output": "pyautogui.hotkey('win', 'discord')"
                },
                {
                    "user_input": "Type hello",
                    "command_output": "pyautogui.typewrite(\"hello\")"
                },
                {
                    "user_input": "What do you see?",
                    "command_output": "print(\"I see a Windows 10 desktop with Chrome browser open\")"
                }
            ],
            "instructions": {
                "primary": "Convert user instructions into precise system commands",
                "format": "Return only the executable command with no additional text",
                "error_handling": "If unable to determine a command, return a specific error message"
            },
            "user_input": user_prompt
        }
    
    def _get_function_declarations(self) -> List[Dict[str, Any]]:
        """Get function declarations for structured command generation."""
        return [
            {
                "name": "execute_mouse_movement",
                "description": "Move the mouse cursor to specific coordinates and perform an action",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer",
                            "description": "X coordinate on screen"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate on screen"
                        },
                        "duration": {
                            "type": "number",
                            "description": "Duration of movement in seconds"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["click", "right_click", "double_click", "hover"],
                            "description": "Mouse action to perform"
                        }
                    },
                    "required": ["x", "y", "action"]
                }
            },
            {
                "name": "execute_keyboard_input",
                "description": "Simulate keyboard input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "special_keys": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Special keys to press (e.g., ctrl, alt)"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "execute_hotkey",
                "description": "Simulate pressing a hotkey combination",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Keys to press simultaneously"
                        }
                    },
                    "required": ["keys"]
                }
            },
            {
                "name": "start_application",
                "description": "Start an application or open a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the application or file"
                        },
                        "arguments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Command line arguments"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "print_output",
                "description": "Print information to the console",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to print"
                        }
                    },
                    "required": ["text"]
                }
            }
        ] 