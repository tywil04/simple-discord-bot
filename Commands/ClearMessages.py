Name = "Clear Messages";
HelpString = "Run `/clearmessages` and follow the on-screen instructions. This will clear the specified number of messages in the channel where the command was invoked.";
Description = "Clears a specified number of messages in the channel where the command was invoked."

def Init(Discord, Config, Bot, Database):
    class ClearMessagesModal(Discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title);

            self.NumberOfMessages = Discord.ui.InputText(label="Number of messages to delete", placeholder="10", style=Discord.InputTextStyle.short, max_length=50);

            self.add_item(self.NumberOfMessages);

        async def callback(self, interaction):
            try:
                NumberOfMessages = int(self.NumberOfMessages.value.strip());
                await interaction.channel.purge(limit=NumberOfMessages);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully cleared the last {NumberOfMessages} messages.", color=Config.Colours.Positive), ephemeral=True);
            except: await interaction.response.send_message(embed=Discord.Embed(description="Error when parsing provided number of messages to delete. Did you include any non-digit characters?", color=Config.Colours.Negative), ephemeral=True);

    @Bot.slash_command(description=Description)
    async def clearmessages(context):
        if context.author.guild_permissions.administrator:
            Modal = ClearMessagesModal(title="Clear Messages");
            await context.interaction.response.send_modal(Modal);
        else:
            await context.interaction.response.send_message(embed=Discord.Embed(description="Missing required permission `Administrator`.", color=Config.Colours.Negative), ephemeral=True);
