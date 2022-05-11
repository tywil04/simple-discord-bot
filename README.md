# Simple Discord Bot

This is a simple discord bot written in python using PyCord.

## Usage
To use the bot, clone this repository and make sure you have Python3 installed and the latest version of PyCord.

Once you have the code locally, you need to do a few things beforehand to get the bot up and running:
  - Create a sqlite3 database
  - Enter your bot details and database path into `Config.py`
  - Run `Bot.py`

This bot uses Discords `/` commands which means that global commands can take up to an hour to register so you will need to wait before you can use the commands on the bot.

## Default Commands
- `ClearMessages.py`: Clears a specified number of messages in the channel where the bot was invoked.
- `CoinFlip.py`: Randomly flips a coin and returns either "Heads" or "Tails".
- `NewCountdown.py`: Creates a countdown which prompts the user to give a time. Users can subscribe to get a end notification.
- `NewGiveaway.py`: Creates a giveaway that people can enter in. Once ended, a random user will be selected.
- `NewPoll.py`: Creates a poll that users can vote with. (Votes can be changed after they have been made).
- `NewRoleProvider.py`: Creates a message that gives/removes a users role when the interact.
- `Ping.py`: Test if the bot is responsive.

Help is a built in command that cannot be disabled. The above commands can be removed by clearing the reference in `Config.py` - you dont have to remove the file (if you do, the reference still needs to be removed from `Config.py`).

## Commands
Commands are just python files that are stored somewhere (by default the folder Commands). To register a command you must import it and add it to the `Commands` array in `Config.py`. Commands must follow this format below.

```python3
Name = "Test";
HelpString = "Test Command"
Description = "Runs a Test Command"

def Init(Discord, Config, Bot, Database):
  @Bot.slash_command(description=Description)
  async def testcommand(context):
    # Your bot code
```

As you can see via the above example, every command has access to the running PyCord instance as `Discord`, the configuration file as `Config`, the running bot instance as `Bot` and an initialised Sqlite3 database as `Database`.

**WARNING**: Only use commands from people you trust or commands you have vetted. Any command has access to `Config.py` which contains your bot token. With a bot token, any malicious actor can do what they wish with your bot. If your bot token has been compromised you need to regenerate it via discords developer website.
