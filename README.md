# Guess-Game-Bot

A modular, scalable Telegram bot for social deduction and party games.

## Project Structure

```
guess-game-bot/
├── bot/
│   ├── core/                     # Game engine components (base classes, player/phase management)
│   │   ├── base_game.py
│   │   ├── player_manager.py
│   │   └── phase_manager.py
│   ├── games/                    # Individual game implementations
│   │   └── impostor_game/
│   │       ├── __init__.py
│   │       ├── impostor_logic.py
│   │       ├── ai_clue_engine.py
│   │       ├── emergency.py
│   │       ├── voting.py
│   │       └── kill.py
│   ├── handlers/                 # Telegram command, callback, and message handlers
│   │   ├── command_handlers.py
│   │   ├── callback_handlers.py
│   │   └── message_handlers.py
│   ├── constants.py              # Shared constants/messages
│   ├── game_manager.py           # Game selection and routing
│   ├── __init__.py
│   └── utils.py                  # Shared utility functions (AI, helpers)
├── main.py                       # Entry point
├── requirements.txt
├── README.md
└── tests/
    └── ... (test modules per feature)
```

## Key Modules
- **bot/core/**: Abstract base classes and managers for game logic.
- **bot/games/impostor_game/**: All logic and phases for the Impostor Game.
- **bot/handlers/**: Telegram bot handlers for commands, callbacks, and messages.
- **bot/constants.py**: Shared messages and constants.
- **bot/game_manager.py**: Manages which game is active and routes commands.
- **bot/utils.py**: Shared utility functions (AI, helpers).
- **tests/**: Unit and integration tests for all features.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Abel5173/Guess-Game-Bot.git
   cd Guess-Game-Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with the following content:
   ```plaintext
   HF_API_KEY=your_huggingface_api_key
   BOT_TOKEN=your_telegram_bot_token
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Usage

- **Start the bot in a group chat:**
  ```plaintext
  /startgame
  ```
- **Select a game:**
  - Guess Game: Click "Guess Game" and follow the instructions.
  - Impostor Game: Click "Impostor Game" and follow the instructions.

## Folder Structure

```
Guess-Game-Bot/
├── bot/
│   ├── __init__.py
│   ├── guess_game.py
│   ├── impostor_game.py
│   ├── game_manager.py
│   └── utils.py
├── main.py
├── requirements.txt
├── .env
├── README.md
└── tests/
    ├── __init__.py
    ├── test_guess_game.py
    └── test_impostor_game.py
```

## Contributing

Feel free to open issues or pull requests if you find any bugs or have suggestions for improvements.

## License

MIT 

## Docker Deployment

You can run the bot in a containerized environment using Docker:

1. **Copy the example environment file and fill in your secrets:**
   ```bash
   cp .env.example .env
   # Edit .env and set your BOT_TOKEN and HF_API_KEY
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t guess-game-bot .
   ```

3. **Run the bot:**
   ```bash
   docker run --env-file .env guess-game-bot
   ```

This will start the bot in a container, using the environment variables from your `.env` file.

## Production Notes
- Make sure your `.env` file is never committed to version control.
- For persistent data, mount a volume for the SQLite database or use a managed database (Postgres, etc) in production.
- For cloud deployment (Heroku, Render, etc), set the environment variables in the platform's dashboard.

--- 