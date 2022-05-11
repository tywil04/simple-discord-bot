Name = "Coin Flip";
HelpString = "Run `/coinflip` and the bot will randomly reply with `Heads` or `Tails`.";
Description = "Makes the bot randomly reply with 'Heads' or 'Tails'.";

import random;

def Init(Discord, Config, Bot, Database):
    @Bot.slash_command(description=Description)
    async def coinflip(context):
        SystemRandom = random.SystemRandom();
        await context.respond(embed=Discord.Embed(description=SystemRandom.choice(["Heads", "Tails"]), color=Config.Colours.Positive));