import os
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess
import mss
import mss.tools
import pyautogui
import time
import base64
from io import BytesIO
import tempfile
import re
import tkinter as tk
from tkinter import simpledialog

load_dotenv()

def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            load_dotenv('credentials.env')
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not found in credentials.env")
        except Exception as e:
            raise ValueError(f"Error loading API key from credentials.env: {e}")
    return api_key

genai.configure(api_key=get_gemini_api_key())
model = genai.GenerativeModel('gemini-1.5-flash')

def capture_screenshot():
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])  # Monitor number
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
             mss.tools.to_png(sct_img.rgb, sct_img.size, output=tmp_file.name)
             with open(tmp_file.name, "rb") as img_file:
                 img_bytes = img_file.read()
        os.unlink(tmp_file.name)
        return base64.b64encode(img_bytes).decode('utf-8')


def analyze_image_and_generate_command(user_prompt, image_base64, retry=False):
    """Generates system command based on user prompt and visual analysis."""

    gemini_prompt = f"""
    You are a system command translator designed to operate on a Windows 10 64-bit (x64) architecture. Before generating commands, understand that:

    *   **System Architecture:** You are running on a Windows 10 64-bit (x64) operating system. This means:
        *   Most applications will be located in directories such as "C:/Program Files" or "C:/Program Files (x86)".
        *   The user can access the start menu by pressing the windows key.
        *  The user can use `win + number` to open an app located in the taskbar with that particular order.
    *   **General Guides:**
         *  If the user is trying to open chrome use: `start "C:/Program Files/Google/Chrome/Application/chrome.exe"` If that command fails then try `pyautogui.hotkey('win', 'chrome')`.
         * If the user is trying to open notepad use: `start "C:/Windows/System32/notepad.exe"` If that command fails then try `pyautogui.hotkey('win', 'notepad')`.
         * If the user is trying to open discord use: `pyautogui.hotkey('win', 'discord')`. If the path of an application is known, then use the start command instead of the windows search command. For example if the path of discord is known use `start "C:/path/to/discord.exe"`.
         * If the user is trying to open any application that is not chrome, discord or notepad, then use windows search to open it, for example `pyautogui.hotkey('win', 'whatsapp')`.
        *   Use `pyautogui.moveTo(x, y, duration=0.1); pyautogui.click()` to simulate mouse clicks.
        *   Use `pyautogui.typewrite("text")` to simulate text input.
        *   To simulate the windows key plus a number, the command should be `pyautogui.hotkey('win', 'number')`, For example `pyautogui.hotkey('win', '5')`
        *  Do not use `mouse.move()`.
    *   **Programming Languages:**
        *   Be aware that python code will be interpreted by the python interpreter, which can be launched from the windows command prompt.
        *   If a python file is specified, then you can use the python interpreter with a path to the python file, for example `python "C:/test.py"`.
        * When a prompt asks to print something to the console, use `print("...")` command.
    
    Your task is to convert user instructions into precise system commands, mouse actions, and keyboard actions for the user's Windows 10 x64 system. You will receive a base64 encoded screenshot of a Windows 10 screen, analyze its contents, and output *only* the necessary commands, without explanations, surrounding text, or code formatting such as ```python, ```, or anything else.

    Here's a detailed breakdown of your capabilities and instructions:

    1.  **Screenshot Analysis:** Carefully analyze the provided screenshot of the user's Windows 10 monitor. Identify elements like icons, buttons, or text that are relevant to the user's prompt.
    2.  **Precise Command Generation:** Translate the user's request into *only* system commands, mouse actions, and keyboard actions.
       *   For mouse actions, provide the specific `pyautogui.moveTo(x, y, duration=0.1); pyautogui.click()` to simulate mouse clicks. Do not use any other type of mouse commands.
          * For keyboard inputs, use `pyautogui.typewrite("text")` for typing text.
          * To simulate the windows key plus a number, the command should be `pyautogui.hotkey('win', 'number')`, For example `pyautogui.hotkey('win', '5')`
          *  If the user is trying to open chrome use: `start "C:/Program Files/Google/Chrome/Application/chrome.exe"` If that command fails then try `pyautogui.hotkey('win', 'chrome')`.
           * If the user is trying to open notepad use: `start "C:/Windows/System32/notepad.exe"` If that command fails then try `pyautogui.hotkey('win', 'notepad')`.
          * If the user is trying to open discord use: `pyautogui.hotkey('win', 'discord')`. If the path of an application is known, then use the start command instead of the windows search command. For example if the path of discord is known use `start "C:/path/to/discord.exe"`.
          *  If the user is trying to open any application that is not chrome, discord or notepad, then use windows search to open it, for example `pyautogui.hotkey('win', 'whatsapp')`
        *  If the prompt asks what you see, then do not provide a detailed explanation. You should respond with `print("...")` where "..." is a brief overview of the main elements in the image.
        *   Do not use `mouse.move()`.
    3.  **Contextual Awareness:** Understand the context of the user's prompt, taking into account the current state of the Windows 10 desktop.
     4.  **Error Handling:** If you encounter an error, or cannot fulfill the user's request,  and the retry flag is not set return an error message that says `An error occurred, retrying...` followed by an empty line and no other text. When the retry flag is set, then return a command like `print("An error occurred")`. The error must be a single line.
    5.  **Absolute Precision:** Do not include any text besides the commands themselves. No preambles, explanations, or surrounding text. There should not be any code formatting such as ```python, ``` or any other text. The command must be executable on Windows 10.

        Example:
             User: Click on the save button
             Response: pyautogui.moveTo(50, 100, duration=0.1); pyautogui.click()
             User: Open Chrome
             Response: start "C:/Program Files/Google/Chrome/Application/chrome.exe"
             User: Open Discord
             Response: pyautogui.hotkey('win', 'discord')
             User: Type hello
             Response: pyautogui.typewrite("hello")
             User: Do windows + 5
             Response: pyautogui.hotkey('win', '5')
             User: What do you see?
             Response: print("I see a Windows 10 desktop")
        Important Instructions:
         1. Do not generate unsafe code.
         2. Output *only* commands. There should not be any surrounding text, explanation, or formatting. You should not output any code blocks or anything else that is not the specific command itself.
    Now provide the following:
        User: {user_prompt}
        Screenshot: {image_base64}
        Response: """

    try:
      
        response = model.generate_content(
            contents=[
                gemini_prompt,
                 {
                    "mime_type": "image/png",
                    "data": image_base64
                },
            ]
        )
        
        command_response = response.text.strip()
        return command_response
    except Exception as e:
        if not retry:
            return "An error occurred, retrying..."
        else:
            return "print('An error occurred')"
    

def execute_command_response(command_response, user_prompt, retry=False):
    command_lines = command_response.split(';')
    for command_line in command_lines:
        command_line = command_line.strip()
        if command_line.startswith("pyautogui.moveTo"):
            try:
                parts = command_line[len("pyautogui.moveTo("):-1].split(',')
                x = int(parts[0].strip())
                y = int(parts[1].strip())
                duration_part = parts[2].strip().split('=')
                duration = float(duration_part[1].strip())
                pyautogui.moveTo(x,y, duration=duration)
                time.sleep(0.2)
            except Exception as e:
               print("Error parsing pyautogui.moveTo command:", e)
        elif command_line.startswith("pyautogui.click()"):
             try:
                pyautogui.click()
             except Exception as e:
                print("Error parsing pyautogui.click command", e)
        elif command_line.startswith("pyautogui.typewrite"):
            try:
                text = command_line[len("pyautogui.typewrite("):-1]
                text = re.sub(r'^"|"$', '', text)
                pyautogui.typewrite(text)
            except Exception as e:
                print("Error executing pyautogui.typewrite command:",e)
        elif command_line.startswith("pyautogui.hotkey"):
           try:
                command = command_line[len("pyautogui.hotkey("):-1].split(',')
                key1 = command[0].strip().replace("'", "")
                key2 = command[1].strip().replace("'", "")
                pyautogui.hotkey(key1, key2)
                time.sleep(0.2)
           except Exception as e:
               print("Error parsing pyautogui.hotkey command", e)
        elif command_line.startswith("start "):
            try:
                command = command_line[len("start "):]
                process = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            except subprocess.CalledProcessError as e:
                print(f"Error executing start command: {e.stderr.strip()}")
                if not retry:
                    return "An error occurred, retrying..."
        elif command_line.startswith("print("):
            try:
                text = command_line[len("print("):-1]
                text = re.sub(r'^"|"$', '', text)
                print(text)
            except Exception as e:
                print(f"Error executing print command",e)
        elif command_line:
            print("Unrecognized command:", command_line)
            if not retry:
                 return "An error occurred, retrying..."
    return ""

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    while True:
        user_prompt = simpledialog.askstring("Input", "How can I help you?")
        if user_prompt is None or user_prompt.lower() == "exit":
            print("Exiting...")
            break
        
        image_base64 = capture_screenshot()
        if image_base64:
           command_response = analyze_image_and_generate_command(user_prompt, image_base64)
           print(command_response)
           if command_response.startswith("An error occurred, retrying..."):
                print("Retrying...")
                time.sleep(0.5) # Wait half a second for any UI to settle.
                image_base64 = capture_screenshot()
                if image_base64:
                   command_response = analyze_image_and_generate_command(user_prompt, image_base64, True) # Set retry = True
                   print(command_response)
                   if not command_response.startswith("print("):
                      print("Executing command after retry...")
                      execute_command_response(command_response,user_prompt, True)
                   else:
                        print("Command generation failed:", command_response)
                else:
                    print("Failed to capture screenshot on retry")
           elif not command_response.startswith("An error"):
                print("Executing command...")
                execute_command_response(command_response,user_prompt)
           else:
               print("Command generation failed:", command_response)
        else:
             print("Failed to capture screenshot.")