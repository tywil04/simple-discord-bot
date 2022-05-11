# Imports
import discord as Discord;
import Config;
import sqlite3 as SQLite3;

# Config
Database = SQLite3.connect(Config.DatabasePath);

Bot = Discord.Bot(intents=Discord.Intents().all(), activity=Discord.Activity(type=Config.ActivityPrefix, name=Config.ActivityString));

CommandsOnReady = [];
for Command in Config.Commands:
    Maybe = Command.Init(Discord, Config, Bot, Database)
    if Maybe != None:
        CommandsOnReady.append(Maybe);

@Bot.event
async def on_ready():
    print(f"Logged in as {Bot.user}")

    for CommandOnReady in CommandsOnReady:
        await CommandOnReady(Discord, Config, Bot, Database);

@Bot.event
async def on_raw_message_delete(context):
    try:
        Database.execute(f"DELETE FROM RoleProviders WHERE MessageId = {context.message_id} AND GuildId = {context.guild_id} AND ChannelId = {context.channel_id}");
        Database.execute(f"DELETE FROM Polls WHERE MessageId = {context.message_id} AND GuildId = {context.guild_id} AND ChannelId = {context.channel_id}");
        Database.execute(f"DELETE FROM Countdowns WHERE MessageId = {context.message_id} AND GuildId = {context.guild_id} AND ChannelId = {context.channel_id}");
        Database.execute(f"DELETE FROM CountdownMentions WHERE MessageId = {context.message_id}");
        Database.commit();
    except: pass;

@Bot.slash_command(description="Returns a helpful message.")
async def help(context):
    Embed = Discord.Embed(color=Config.Colours.Positive);
    for Command in Config.Commands:
        Embed.add_field(name=Command.Name, value=Command.HelpString, inline=False);
    Embed.set_footer(text=Config.HelpFooter);
    await context.respond(embed=Embed, ephemeral=True);

# remove unused guild data;
# rearange db

Bot.run(Config.BotToken);