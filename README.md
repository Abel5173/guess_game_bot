# Guess-Game-Bot

A Telegram bot that supports two games: Guess Game and Impostor Game.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Guess-Game-Bot.git
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