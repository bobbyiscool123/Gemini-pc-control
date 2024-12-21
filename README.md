# Gemini-Powered Windows Automation

This project leverages the power of Google's Gemini AI model to enable natural language-driven automation of a Windows 10 environment. It interprets user prompts, analyzes screen captures, and translates requests into executable system commands, mouse actions, and keyboard inputs.

## Features

- **Natural Language Interface:** Interact with your Windows desktop using simple, conversational commands.
- **Visual Context:** The application analyzes screenshots to understand the current state of your desktop, ensuring accurate command execution.
- **Automated Actions:** Performs mouse clicks, keyboard inputs, application launches, and more.
- **Error Handling & Retries:** Implements robust error handling and retry mechanisms for better reliability.
- **Optimized for Python 3.13.1:** Written with performance and efficiency in mind, leveraging the latest features of Python 3.13.1 where applicable.

## Getting Started

### Prerequisites

1.  **Python 3.13.1:** This project is optimized for Python 3.13.1. Ensure you have it installed.

    *   **Installation:** Download from the [official Python website](https://www.python.org/downloads/) or use your system's package manager.
2.  **Pip (Python Package Installer):** Should come bundled with Python 3.13.1
3.  **Git:** For cloning the repository (if applicable).
4.  **Google Gemini API Key:** Obtain an API key from the [Google AI Studio](https://aistudio.google.com/). You will need to store it in your `.env` file or in the `credentials.env` file as `GEMINI_API_KEY=your_api_key`.

### Installation

1.  **Clone the Repository (Optional):**

    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3. **Install Required Packages**

    ```bash
        pip install -r requirements.txt
    ```

    If the `requirements.txt` file does not exist then:

    ```bash
    pip install google-generativeai python-dotenv mss pyautogui tkinter
    ```

4.  **Set Up Environment Variables:**

    *   Create a `.env` file or a `credentials.env` file in the root of your project directory and add your Gemini API key:

        ```
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        ```

        *  If a `.env` file exists, then the `GEMINI_API_KEY` must be in that file.
        *  If the `.env` file does not exist and a `credentials.env` file exists, then the `GEMINI_API_KEY` must be in that file.

### Usage

1.  **Run the Script:**
    ```bash
    python your_script_name.py
    ```
    (Replace `your_script_name.py` with the actual name of your main script).
2.  **Follow the Prompts:** A dialog box will appear asking how you want to interact with your computer. Enter your commands.

## Code Overview

- `capture_screenshot()`: Captures a screenshot of the primary monitor using `mss` library and encodes it in base64.
- `analyze_image_and_generate_command()`: Sends a user's prompt along with the screen capture to the Google Gemini model and receives commands.
- `execute_command_response()`: Parses the response from the Google Gemini model and executes the commands.
- The main execution loop in `if __name__ == "__main__":`: The main loop that captures screenshots, receives user prompts, sends them to the Gemini model, and executes the commands.

## Performance Notes for Python 3.13.1

This project is designed to work efficiently within the Python 3.13.1 ecosystem. Here are some key areas and best practices:

-   **Library Optimization:** This project utilizes optimized libraries like `mss` for fast screen captures and `pyautogui` for efficient UI interactions.
-   **Minimal Overhead:** The codebase minimizes unnecessary operations, reducing overhead.
-   **Fast JSON Handling:** We are leveraging `json` which is optimized for faster parsing for efficient data transfer with the Google Gemini API.
-   **Asynchronous Operations:** Async operations should be considered for any function that could potentially block and lead to slower performance.
-   **String Handling:** Instead of concatenating strings, consider using f-strings or the `.format()` function for more efficient string construction.
-   **Profiling:** Profile sections of the code to determine performance bottlenecks and implement changes as needed to improve the performance.

## Contributing

Contributions are welcome! If you would like to improve the project, please follow these steps:
- Fork the repository.
- Create a new branch for your changes.
- Implement your changes.
- Open a pull request with a clear description of your updates.

## License

[Specify your project's license here. For example, MIT License.]

---

**Note**: Replace `your-username/your-repository.git` with the actual URL of your git repository and `your_script_name.py` with the name of your main script.