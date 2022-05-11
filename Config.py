#Discord.py
import discord as Discord;

#General Settings
BotToken = "" # Bot token string required;
BotId = 0 # Bot id integer required;
DatabasePath = "" # Path so sqlite3 database;
ActivityPrefix = Discord.ActivityType.watching # Discord activity;
ActivityString = "For Commands";
CaseInsensitive = True;

ErrorFooter = "Need more help? Try the help command.";
HelpFooter = "All commands are case insensitive.";

#Error Messages
class ErrorMessages():
    TooManyArguments = "Too many arguments provided.";
    TooFewArguments = "Too few arguments provided.";
    CommandNotFound = "Command `{}` not found.";

#Colours
class Colours():
    Positive = 0x0A84FF; #Blue
    Negative = 0xFF453A; #Red

#Active Commands
from Commands import NewRoleProvider, Ping, ClearMessages, NewCountdown, NewGiveaway, CoinFlip, NewPoll;

Commands = [
    NewRoleProvider,
    NewPoll,
    NewCountdown,
    NewGiveaway,
    ClearMessages,
    CoinFlip,
    Ping,
];