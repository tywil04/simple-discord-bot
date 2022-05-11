# Simple Discord Bot

This is a simple discord bot written in python using PyCord.

## Usage
To use the bot, clone this repository and make sure you have Python3 installed and the latest version of PyCord.

Once you have the code locally, you need to do a few things beforehand to get the bot up and running:
  - Create a sqlite3 database
  - Enter your bot details and database path into Config.py

# Commands
Commands are just python files that are stored somewhere (by default Commands). To register a command you must import it and add it to the `Commands` array in Config.py. Commands must follow this format below.

```python3
Name = "Test";
HelpString = "Test Command"
Description = "Runs a Test Command"

def Init(Discord, Config, Bot, Database):
  @Bot.slash_command(description=Description)
  async def testcommand(context):
    # Your bot code
```
