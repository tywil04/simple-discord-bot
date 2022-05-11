Name = "Ping";
HelpString = "Run `/ping` to make the bot reply with `Pong`.";
Description = "Makes the bot reply with 'Pong!'."

def Init(Discord, Config, Bot, Database):
    @Bot.slash_command(description=Description)
    async def ping(context):
        await context.respond(embed=Discord.Embed(description="Pong!", color=Config.Colours.Positive), ephemeral=True);