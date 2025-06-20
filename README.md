# MultiModalMan - Interactive Multimodal Hangman Game

MultiModalMan is an interactive, multi-modal Hangman game that combines various input methods—such as voice, text, and hand gesture recognition—to create an engaging and accessible gameplay experience. Designed to demonstrate the power of multimodal interfaces, the game allows players to guess letters using different modes of communication, enhancing usability and immersion while showcasing the integration of multiple AI and input processing techniques.

## Features

- Multiple input methods:
  - Text input through chat
  - Voice recognition for verbal letter guessing
  - Hand drawing recognition
- Interactive hangman visuals
- AI agent as the game master
- Real-time feedback and game state updates

## Prerequisites

- Python 3.10 or higher
- macOS, Windows, or Linux
- Webcam (for hand gesture recognition)
- Microphone (for voice input)
- OpenAI API key (for the agent functionality)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
```

### 2. Set up a virtual environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key_here
```

Replace `your_openai_api_key_here` with your actual OpenAI API key. You can get one at [OpenAI's platform](https://platform.openai.com/).

## Running the Application

To start the application, run the following command from the project's root directory:

```bash
flet run frontend/main.py --web
```

This will launch the application in your default web browser. The `--web` parameter ensures that the app opens as a web application rather than a desktop window.

## How to Play

1. When the game starts, you'll be greeted by the AI agent.
2. Choose how the word will be selected:
   - Let the AI agent choose a random word
   - Input your own word
3. Start guessing letters using any of the available input methods:
   - Type a letter in the chat
   - Say "I want to use voice input" and then speak a letter
   - Say "I want to draw a letter" and draw the letter with your hand
4. To switch between input methods at any time, just say the corresponding phrase
5. The game will update after each guess, showing:
   - The current state of the word
   - The hangman visual
   - Remaining attempts
6. Continue guessing until you either:
   - Successfully guess the word (win)
   - Run out of attempts (lose)
7. After a game ends, you can choose to play again

## Project Structure

- `frontend/`: The web-based user interface
  - `main.py`: Entry point for the application
  - `src/`: Source code for the frontend
    - `app/`: Game logic and state management
    - `components/`: UI components
    - `config/`: Configuration settings
- `backend/`: Backend services
  - `models/`: Machine learning models
  - `src/`: Backend service implementations
- `controller/`: The AI agent that manages the game
- `docs/`: Documentation files
