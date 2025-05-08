"""Command executor module."""

import re
import subprocess
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple, Union

import pyautogui
from loguru import logger

from gemini_pc_control.logging_config import log_performance
from gemini_pc_control.models.command import (
    Command, CommandType, CommandStatus,
    MouseMoveCommand, MouseClickCommand, KeyboardTypeCommand, KeyboardHotkeyCommand,
    StartProcessCommand, PrintOutputCommand
)
from gemini_pc_control.models.response import AIResponse, ResponseType, FunctionCall


class CommandParser:
    """Parse AI responses into executable commands."""
    
    @log_performance
    def parse_text_response(self, response: AIResponse, user_prompt: str, screenshot_id: Optional[str] = None) -> Command:
        """Parse a text-based AI response into a Command object."""
        command_id = str(uuid.uuid4())
        raw_text = response.raw_text
        
        # Check for special error response
        if raw_text.strip() == "An error occurred, retrying..." or raw_text.startswith("print('An error occurred"):
            logger.warning(f"Detected error response: {raw_text}")
            command = Command(
                id=command_id,
                type=CommandType.UNKNOWN,
                status=CommandStatus.FAILED,
                user_prompt=user_prompt,
                raw_response=raw_text,
                error_message="AI detected an error and suggested retry",
                screenshot_id=screenshot_id
            )
            return command
        
        # Determine command type and create appropriate Command object
        if ';' in raw_text:
            # This is a composite command
            command = Command(
                id=command_id,
                type=CommandType.COMPOSITE,
                user_prompt=user_prompt,
                raw_response=raw_text,
                screenshot_id=screenshot_id
            )
            
            # Split and parse sub-commands
            sub_command_texts = [cmd.strip() for cmd in raw_text.split(';')]
            for sub_text in sub_command_texts:
                if sub_text:  # Skip empty strings
                    sub_command = self._parse_single_command(sub_text, user_prompt, screenshot_id)
                    if sub_command:
                        command.sub_commands.append(sub_command)
        else:
            # Single command
            command = self._parse_single_command(raw_text, user_prompt, screenshot_id)
            if not command:
                # Fallback to unknown command
                command = Command(
                    id=command_id,
                    type=CommandType.UNKNOWN,
                    user_prompt=user_prompt,
                    raw_response=raw_text,
                    screenshot_id=screenshot_id,
                    error_message="Could not parse command"
                )
        
        return command
    
    def _parse_single_command(self, command_text: str, user_prompt: str, screenshot_id: Optional[str] = None) -> Optional[Command]:
        """Parse a single command from text."""
        command_id = str(uuid.uuid4())
        command_text = command_text.strip()
        
        # Mouse move + click
        if command_text.startswith("pyautogui.moveTo"):
            try:
                # Extract coordinates and duration
                match = re.match(r"pyautogui\.moveTo\((\d+),\s*(\d+)(?:,\s*duration=([0-9.]+))?\)", command_text)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                    duration = float(match.group(3)) if match.group(3) else 0.1
                    
                    command = Command(
                        id=command_id,
                        type=CommandType.MOUSE_MOVE,
                        user_prompt=user_prompt,
                        raw_response=command_text,
                        screenshot_id=screenshot_id,
                        data=MouseMoveCommand(x=x, y=y, duration=duration).dict()
                    )
                    return command
            except Exception as e:
                logger.error(f"Error parsing mouse move command: {e}", exc_info=True)
                return None
        
        # Mouse click
        elif command_text.startswith("pyautogui.click"):
            try:
                command = Command(
                    id=command_id,
                    type=CommandType.MOUSE_CLICK,
                    user_prompt=user_prompt,
                    raw_response=command_text,
                    screenshot_id=screenshot_id,
                    data=MouseClickCommand().dict()
                )
                return command
            except Exception as e:
                logger.error(f"Error parsing mouse click command: {e}", exc_info=True)
                return None
        
        # Keyboard type
        elif command_text.startswith("pyautogui.typewrite"):
            try:
                # Extract text
                match = re.match(r'pyautogui\.typewrite\("(.+)"\)', command_text)
                if match:
                    text = match.group(1)
                    command = Command(
                        id=command_id,
                        type=CommandType.KEYBOARD_TYPE,
                        user_prompt=user_prompt,
                        raw_response=command_text,
                        screenshot_id=screenshot_id,
                        data=KeyboardTypeCommand(text=text).dict()
                    )
                    return command
            except Exception as e:
                logger.error(f"Error parsing keyboard type command: {e}", exc_info=True)
                return None
        
        # Keyboard hotkey
        elif command_text.startswith("pyautogui.hotkey"):
            try:
                # Extract keys
                match = re.match(r"pyautogui\.hotkey\((.+)\)", command_text)
                if match:
                    keys_str = match.group(1)
                    keys = [k.strip().strip("'\"") for k in keys_str.split(',')]
                    command = Command(
                        id=command_id,
                        type=CommandType.KEYBOARD_HOTKEY,
                        user_prompt=user_prompt,
                        raw_response=command_text,
                        screenshot_id=screenshot_id,
                        data=KeyboardHotkeyCommand(keys=keys).dict()
                    )
                    return command
            except Exception as e:
                logger.error(f"Error parsing keyboard hotkey command: {e}", exc_info=True)
                return None
        
        # Start process
        elif command_text.startswith("start "):
            try:
                command_str = command_text[len("start "):]
                command = Command(
                    id=command_id,
                    type=CommandType.START_PROCESS,
                    user_prompt=user_prompt,
                    raw_response=command_text,
                    screenshot_id=screenshot_id,
                    data=StartProcessCommand(command=command_str).dict()
                )
                return command
            except Exception as e:
                logger.error(f"Error parsing start process command: {e}", exc_info=True)
                return None
        
        # Print output
        elif command_text.startswith("print("):
            try:
                # Extract text
                match = re.match(r'print\("(.+)"\)', command_text)
                if match:
                    text = match.group(1)
                    command = Command(
                        id=command_id,
                        type=CommandType.PRINT_OUTPUT,
                        user_prompt=user_prompt,
                        raw_response=command_text,
                        screenshot_id=screenshot_id,
                        data=PrintOutputCommand(text=text).dict()
                    )
                    return command
            except Exception as e:
                logger.error(f"Error parsing print command: {e}", exc_info=True)
                return None
        
        return None
    
    @log_performance
    def parse_function_call_response(self, response: AIResponse, user_prompt: str, screenshot_id: Optional[str] = None) -> Command:
        """Parse a function call response into a Command object."""
        command_id = str(uuid.uuid4())
        
        if not response.function_calls:
            logger.warning("No function calls found in response")
            return Command(
                id=command_id,
                type=CommandType.UNKNOWN,
                user_prompt=user_prompt,
                raw_response=response.raw_text,
                screenshot_id=screenshot_id,
                error_message="No function calls found in response"
            )
        
        # If there are multiple function calls, create a composite command
        if len(response.function_calls) > 1:
            command = Command(
                id=command_id,
                type=CommandType.COMPOSITE,
                user_prompt=user_prompt,
                raw_response=response.raw_text,
                screenshot_id=screenshot_id
            )
            
            for func_call in response.function_calls:
                sub_command = self._parse_function_call(func_call, user_prompt, screenshot_id)
                if sub_command:
                    command.sub_commands.append(sub_command)
            
            return command
        
        # Single function call
        return self._parse_function_call(response.function_calls[0], user_prompt, screenshot_id) or Command(
            id=command_id,
            type=CommandType.UNKNOWN,
            user_prompt=user_prompt,
            raw_response=response.raw_text,
            screenshot_id=screenshot_id,
            error_message="Could not parse function call"
        )
    
    def _parse_function_call(self, function_call: FunctionCall, user_prompt: str, screenshot_id: Optional[str] = None) -> Optional[Command]:
        """Parse a single function call into a Command object."""
        command_id = str(uuid.uuid4())
        
        try:
            if function_call.name == "execute_mouse_movement":
                return Command(
                    id=command_id,
                    type=CommandType.MOUSE_MOVE,
                    user_prompt=user_prompt,
                    raw_response=str(function_call.dict()),
                    screenshot_id=screenshot_id,
                    data=MouseMoveCommand(
                        x=function_call.arguments.get("x", 0),
                        y=function_call.arguments.get("y", 0),
                        duration=function_call.arguments.get("duration", 0.1)
                    ).dict()
                )
            
            elif function_call.name == "execute_keyboard_input":
                return Command(
                    id=command_id,
                    type=CommandType.KEYBOARD_TYPE,
                    user_prompt=user_prompt,
                    raw_response=str(function_call.dict()),
                    screenshot_id=screenshot_id,
                    data=KeyboardTypeCommand(
                        text=function_call.arguments.get("text", "")
                    ).dict()
                )
            
            elif function_call.name == "execute_hotkey":
                return Command(
                    id=command_id,
                    type=CommandType.KEYBOARD_HOTKEY,
                    user_prompt=user_prompt,
                    raw_response=str(function_call.dict()),
                    screenshot_id=screenshot_id,
                    data=KeyboardHotkeyCommand(
                        keys=function_call.arguments.get("keys", [])
                    ).dict()
                )
            
            elif function_call.name == "start_application":
                return Command(
                    id=command_id,
                    type=CommandType.START_PROCESS,
                    user_prompt=user_prompt,
                    raw_response=str(function_call.dict()),
                    screenshot_id=screenshot_id,
                    data=StartProcessCommand(
                        command=function_call.arguments.get("path", "")
                    ).dict()
                )
            
            elif function_call.name == "print_output":
                return Command(
                    id=command_id,
                    type=CommandType.PRINT_OUTPUT,
                    user_prompt=user_prompt,
                    raw_response=str(function_call.dict()),
                    screenshot_id=screenshot_id,
                    data=PrintOutputCommand(
                        text=function_call.arguments.get("text", "")
                    ).dict()
                )
            
            else:
                logger.warning(f"Unknown function call: {function_call.name}")
                return None
        
        except Exception as e:
            logger.error(f"Error parsing function call {function_call.name}: {e}", exc_info=True)
            return None


class CommandExecutor:
    """Execute commands on the system."""
    
    def __init__(self):
        """Initialize the command executor."""
        self.parser = CommandParser()
        logger.debug("Initialized command executor")
    
    @log_performance
    def execute_command(self, command: Command) -> bool:
        """Execute a command and update its status."""
        if command.status == CommandStatus.FAILED:
            logger.warning(f"Skipping execution of failed command: {command.id}")
            return False
        
        try:
            command.update_status(CommandStatus.EXECUTING)
            
            if command.type == CommandType.COMPOSITE:
                success = self._execute_composite_command(command)
            else:
                success = self._execute_single_command(command)
            
            if success:
                command.update_status(CommandStatus.COMPLETED)
            else:
                command.update_status(CommandStatus.FAILED, "Command execution failed")
            
            return success
        
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg, exc_info=True, command_id=command.id)
            command.update_status(CommandStatus.FAILED, error_msg)
            return False
    
    def _execute_composite_command(self, command: Command) -> bool:
        """Execute a composite command (multiple sub-commands)."""
        success = True
        
        for sub_command in command.sub_commands:
            sub_success = self._execute_single_command(sub_command)
            success = success and sub_success
            
            if not sub_success and sub_command.type != CommandType.PRINT_OUTPUT:
                logger.warning(f"Sub-command failed, stopping composite execution: {sub_command.id}")
                break
            
            # Add small delay between commands
            time.sleep(0.1)
        
        return success
    
    def _execute_single_command(self, command: Command) -> bool:
        """Execute a single command based on its type."""
        try:
            if command.type == CommandType.MOUSE_MOVE:
                return self._execute_mouse_move(command)
            
            elif command.type == CommandType.MOUSE_CLICK:
                return self._execute_mouse_click(command)
            
            elif command.type == CommandType.KEYBOARD_TYPE:
                return self._execute_keyboard_type(command)
            
            elif command.type == CommandType.KEYBOARD_HOTKEY:
                return self._execute_keyboard_hotkey(command)
            
            elif command.type == CommandType.START_PROCESS:
                return self._execute_start_process(command)
            
            elif command.type == CommandType.PRINT_OUTPUT:
                return self._execute_print_output(command)
            
            else:
                logger.warning(f"Unknown command type: {command.type}")
                return False
        
        except Exception as e:
            logger.error(f"Error executing command {command.id} of type {command.type}: {e}", exc_info=True)
            return False
    
    def _execute_mouse_move(self, command: Command) -> bool:
        """Execute a mouse move command."""
        data = command.data
        x = data.get("x", 0)
        y = data.get("y", 0)
        duration = data.get("duration", 0.1)
        
        logger.debug(f"Moving mouse to ({x}, {y}) with duration {duration}")
        pyautogui.moveTo(x, y, duration=duration)
        return True
    
    def _execute_mouse_click(self, command: Command) -> bool:
        """Execute a mouse click command."""
        data = command.data
        button = data.get("button", "left")
        clicks = data.get("clicks", 1)
        
        logger.debug(f"Clicking mouse with button={button}, clicks={clicks}")
        pyautogui.click(button=button, clicks=clicks)
        return True
    
    def _execute_keyboard_type(self, command: Command) -> bool:
        """Execute a keyboard typing command."""
        data = command.data
        text = data.get("text", "")
        
        if not text:
            logger.warning("Keyboard type command with empty text")
            return False
        
        logger.debug(f"Typing text: {text}")
        pyautogui.typewrite(text)
        return True
    
    def _execute_keyboard_hotkey(self, command: Command) -> bool:
        """Execute a keyboard hotkey command."""
        data = command.data
        keys = data.get("keys", [])
        
        if not keys:
            logger.warning("Keyboard hotkey command with no keys")
            return False
        
        logger.debug(f"Pressing hotkey: {keys}")
        pyautogui.hotkey(*keys)
        return True
    
    def _execute_start_process(self, command: Command) -> bool:
        """Execute a start process command."""
        data = command.data
        command_str = data.get("command", "")
        
        if not command_str:
            logger.warning("Start process command with empty command")
            return False
        
        logger.debug(f"Starting process: {command_str}")
        try:
            subprocess.run(command_str, shell=True, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Process execution error: {e.stderr}")
            return False
    
    def _execute_print_output(self, command: Command) -> bool:
        """Execute a print output command."""
        data = command.data
        text = data.get("text", "")
        
        logger.info(f"Command output: {text}")
        print(text)
        return True
    
    @log_performance
    def execute_ai_response(self, response: AIResponse, user_prompt: str, screenshot_id: Optional[str] = None) -> Tuple[bool, Command]:
        """Parse and execute an AI response."""
        # Parse the response into a command
        if response.is_function_call:
            command = self.parser.parse_function_call_response(response, user_prompt, screenshot_id)
        else:
            command = self.parser.parse_text_response(response, user_prompt, screenshot_id)
        
        # Execute the command
        success = self.execute_command(command)
        
        return success, command 