Name = "New Poll";
HelpString = "Run `/newpoll` and follow the on-screen instructions. This will create a poll with your desired options.";
Description = "Creates a poll.";

def Init(Discord, Config, Bot, Database):
    class PollButton(Discord.ui.Button):
        def __init__(self, label):
            super().__init__(label=label, custom_id=f"'{label}UUID'", style=Discord.ButtonStyle.primary);

        async def callback(self, interaction):
            View = Discord.ui.View(timeout=None);
            Embed = Discord.Embed(title=interaction.message.embeds[0].title, description="To vote/unvote use the buttons below.", color=Config.Colours.Positive);

            RemoveFromOthers = None;
            for EmbedProxy in interaction.message.embeds[0].fields:
                if interaction.user.mention in EmbedProxy.value.split("\n"):
                    RemoveFromOthers = EmbedProxy.name;

            for EmbedProxy in interaction.message.embeds[0].fields:
                if EmbedProxy.name == self.label.replace("Vote ", ""):
                    if EmbedProxy.value == "*No votes*":
                        Embed.add_field(name=EmbedProxy.name, value=f"{interaction.user.mention}\n", inline=False);

                        await interaction.response.send_message(embed=Discord.Embed(description="Successfully voted `{}` for poll `{}`.".format(self.label.replace("Vote ", ""), interaction.message.embeds[0].title), color=Config.Colours.Positive), ephemeral=True);
                    else:
                        People = EmbedProxy.value.split("\n");

                        if interaction.user.mention in People:
                            People.remove(interaction.user.mention);
                            await interaction.response.send_message(embed=Discord.Embed(description="Successfully unvoted `{}` for poll `{}`.".format(self.label.replace("Vote ", ""), interaction.message.embeds[0].title), color=Config.Colours.Positive), ephemeral=True);
                        else:
                            People.append(interaction.user.mention);
                            await interaction.response.send_message(embed=Discord.Embed(description="Successfully voted `{}` for poll `{}`.".format(self.label.replace("Vote ", ""), interaction.message.embeds[0].title), color=Config.Colours.Positive), ephemeral=True);

                        if len(People) == 0:
                            Embed.add_field(name=EmbedProxy.name, value="*No votes*", inline=False);
                        else:
                            Embed.add_field(name=EmbedProxy.name, value="\n".join(People), inline=False);
                else:
                    if RemoveFromOthers != None and EmbedProxy.name == RemoveFromOthers:
                        People = EmbedProxy.value.split("\n");
                        People.remove(interaction.user.mention);

                        if len(People) == 0:
                            Embed.add_field(name=EmbedProxy.name, value="*No votes*", inline=False);
                        else:
                            Embed.add_field(name=EmbedProxy.name, value="\n".join(People), inline=False);
                    else:
                        Embed.add_field(name=EmbedProxy.name, value=EmbedProxy.value, inline=False);

            for Button in interaction.message.components[0].children:
                View.add_item(PollButton(label=Button.label));

            await interaction.message.edit(embed=Embed, view=View);

    class PollModal(Discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title);

            self.PollTitle = Discord.ui.InputText(label="Poll Title", placeholder="Example Poll", style=Discord.InputTextStyle.short, max_length=100);
            self.Options = Discord.ui.InputText(label="Options (Seperate with a comma)", style=Discord.InputTextStyle.long);

            self.add_item(self.PollTitle);
            self.add_item(self.Options);

        async def callback(self, interaction):
            Options = self.Options.value.strip();
            Options = Options.split(",");
            Options = list(filter(None, Options));

            if len(Options) == 0:
                await interaction.response.send_message(embed=Discord.Embed(description=f"No options provided.", color=Config.Colours.Negative), ephemeral=True);
            else:
                CanContinue = True;
                for Option in Options:
                    if Options.count(Option) > 1:
                        try: await interaction.response.send_message(embed=Discord.Embed(description=f"Cannot create poll with duplicate option `{Option}`.", color=Config.Colours.Negative), ephemeral=True);
                        except: pass;
                        CanContinue = False;

                if CanContinue == True:
                    View = Discord.ui.View(timeout=None);
                    Embed = Discord.Embed(title=self.PollTitle.value.strip(), description="To vote/unvote use the buttons below.", color=Config.Colours.Positive);

                    for Option in Options:
                        View.add_item(PollButton(label=f"Vote {Option.strip()}"));
                        Embed.add_field(name=Option.strip(), value="*No votes*", inline=False);

                    Interaction = await interaction.response.send_message(embed=Embed, view=View);
                    Message = await Interaction.original_message();

                    Database.execute(f"INSERT INTO Polls (MessageId, ChannelId, GuildId) VALUES ({Message.id}, {Message.channel.id}, {interaction.guild.id})");
                    Database.commit();

    @Bot.slash_command(description=Description)
    async def newpoll(context):
        Modal = PollModal(title="New Poll");
        await context.interaction.response.send_modal(Modal);

    async def OnReady(Discord, Config, Bot, Database):
        for Guild in Bot.guilds:
            CollectedData = Database.execute(f"SELECT MessageId, ChannelId FROM Polls WHERE GuildId = {Guild.id}").fetchall();
            for Data in CollectedData:
                MessageId = Data[0];
                ChannelId = Data[1];
                PartialMessage = Bot.get_partial_messageable(ChannelId);

                try:
                    Message = await PartialMessage.fetch_message(MessageId);

                    import copy;

                    NewEmbed = copy.copy(Message.embeds[0]);
                    View = Discord.ui.View(timeout=None);

                    for Button in Message.components[0].children:
                        View.add_item(PollButton(label=Button.label));

                    #await Message.edit(embed=NewEmbed);
                    await Message.edit(embed=NewEmbed, view=View);
                except Discord.errors.NotFound:
                    Database.execute(f"DELETE FROM Polls WHERE MessageId = {MessageId} AND GuildId = {Guild.id} AND ChannelId = {ChannelId}");
                    Database.commit();

    return OnReady;