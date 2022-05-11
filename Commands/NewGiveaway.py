Name = "New Giveaway";
HelpString = "Run `/newgiveaway` and follow the on-screen instructions. This will create a giveaway that allows users to enter. When the giveaway ends, a random user who entered will be picked.";
Description = "Creates a giveaway that randomly picks a winner."

import asyncio
import random;
import time;
import copy;

def Init(Discord, Config, Bot, Database):
    async def GiveawayBackgroundTask(EndTime, SendObject, Message, NotificationButton, GuildId):
        if EndTime <= time.time():
            NewEmbed = copy.copy(Message.embeds[0]);
            NewEmbed.description = f"Giveaway over!";

            await Message.edit(embed=NewEmbed, view=None);

            SystemRandom = random.SystemRandom();
            Winner = SystemRandom.choice(NotificationButton.ToMention);

            await SendObject.send(content=Winner, embed=Discord.Embed(
                description=f"The giveaway `{NewEmbed.title}` has finished and {Winner} has won.",
                color=Config.Colours.Positive,
            ));

            Database.execute(f"DELETE FROM Giveaways WHERE MessageId = {Message.id} AND GuildId = {GuildId}");
            Database.execute(f"DELETE FROM GiveawayMentions WHERE MessageId = {Message.id}");
            Database.commit();
        else:
            Minutes, Seconds = divmod(EndTime - time.time(), 60)
            Hours, Minutes = divmod(Minutes, 60)
            Days, Hours = divmod(Hours, 24)

            NewEmbed = copy.copy(Message.embeds[0]);
            NewEmbed.description = f"Use the `Enter Giveaway` button below to enter into the giveaway.\n\nTime remaining:\nDay(s): **{int(Days)}**\nHour(s): **{int(Hours)}**\nMinute(s): **{int(Minutes)}**";

            NewView = Discord.ui.View(timeout=None);
            NewButton = GiveawayButton(label=Message.components[0].children[0].label, giveawayname=NewEmbed.title, tomention=NotificationButton.ToMention);
            NewView.add_item(NewButton);

            if NewEmbed.description != Message.embeds[0].description:
                await Message.edit(embed=NewEmbed, view=NewView);

            await asyncio.sleep(15);

            Bot.loop.create_task(GiveawayBackgroundTask(EndTime, SendObject, Message, NewButton, GuildId));

    class GiveawayButton(Discord.ui.Button):
        def __init__(self, label, giveawayname, tomention=[]):
            super().__init__(label=label, custom_id=f"'{label}UUID'", style=Discord.ButtonStyle.primary);
            self.ToMention = tomention;
            self.GiveawayName = giveawayname;

        async def callback(self, interaction):
            if interaction.user.mention in self.ToMention:
                self.ToMention.remove(interaction.user.mention);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully removed you into the giveaway `{self.GiveawayName}`", color=Config.Colours.Positive), ephemeral=True);
                Database.execute(f"DELETE FROM GiveawayMentions WHERE MessageId = {interaction.message.id} AND UserMention = '{interaction.user.mention}'");
                Database.commit();
            else:
                self.ToMention.append(interaction.user.mention);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully entered you into the giveaway `{self.GiveawayName}`.", color=Config.Colours.Positive), ephemeral=True);
                if not interaction.user.mention in [UserMention[0] for UserMention in Database.execute(f"SELECT UserMention FROM GiveawayMentions WHERE MessageId = {interaction.message.id}").fetchall()]:
                    Database.execute(f"INSERT INTO GiveawayMentions (MessageId, UserMention) VALUES ({interaction.message.id}, '{interaction.user.mention}')");
                    Database.commit();

    class GiveawayModal(Discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title);

            self.GiveawayTitle = Discord.ui.InputText(label="Giveaway Title", placeholder="Example Giveaway", style=Discord.InputTextStyle.short, max_length=100);
            self.GiveawayDays = Discord.ui.InputText(label="Days until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);
            self.GiveawayHours = Discord.ui.InputText(label="Hours until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);
            self.GiveawayMinutes = Discord.ui.InputText(label="Minutes until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);

            self.add_item(self.GiveawayTitle);
            self.add_item(self.GiveawayDays);
            self.add_item(self.GiveawayHours);
            self.add_item(self.GiveawayMinutes);

        async def callback(self, interaction):
            try:
                Minutes = int(self.GiveawayMinutes.value or 0);
                Hours = int(self.GiveawayHours.value or 0);
                Days = int(self.GiveawayDays.value or 0);

                if Minutes == 0 and Hours == 0 and Days == 0:
                    await interaction.response.send_message(embed=Discord.Embed(description="No time provided.", color=Config.Colours.Negative), ephemeral=True);
                else:
                    if Minutes > 60:
                        DivisionFloor, DivisionMod = divmod(Minutes, 60);
                        Hours += DivisionFloor;
                        Minutes = DivisionMod;

                    if Hours > 24:
                        DivisionFloor, DivisionMod = divmod(Hours, 24);
                        Days += DivisionFloor;
                        Hours = DivisionMod;

                    EndTime = time.time() + (86400 * Days) + (3600 * Hours) + (60 * Minutes);

                    NotificationSubscribeButton = GiveawayButton(label="Enter Giveaway", giveawayname=self.GiveawayTitle.value.strip());
                    View = Discord.ui.View(NotificationSubscribeButton, timeout=None);
                    Embed = Discord.Embed(title=self.GiveawayTitle.value.strip(), description=f"Use the `Enter Giveaway` button below to enter into the giveaway.\n\nTime remaining:\nDay(s): **{int(Days)}**\nHour(s): **{int(Hours)}**\nMinute(s): **{int(Minutes)}**", color=Config.Colours.Positive);
                    Giveaway = await interaction.response.send_message(embed=Embed, view=View);
                    GiveawayMessage = await Giveaway.original_message();

                    Database.execute(f"INSERT INTO Giveaways (MessageId, ChannelId, GuildId, EndTime) VALUES ({GiveawayMessage.id}, {GiveawayMessage.channel.id}, {interaction.guild.id}, {EndTime})");
                    Database.commit();

                    Bot.loop.create_task(GiveawayBackgroundTask(EndTime, interaction.followup, GiveawayMessage, NotificationSubscribeButton, interaction.guild.id));
            except: await interaction.response.send_message(embed=Discord.Embed(description="Error when parsing provided time. Did you include any non-digit characters?", color=Config.Colours.Negative), ephemeral=True);

    @Bot.slash_command(description=Description)
    async def newgiveaway(context):
        if context.author.guild_permissions.administrator:
            if len(Database.execute(f"SELECT MessageId FROM Giveaways WHERE GuildId = {context.guild.id}").fetchall()) < 5:
                Modal = GiveawayModal(title="New Giveaway");
                await context.interaction.response.send_modal(Modal);
            else:
                await context.interaction.response.send_message(embed=Discord.Embed(description="This guild already has `5` active giveaways.", color=Config.Colours.Negative), ephemeral=True);
        else:
            await context.interaction.response.send_message(embed=Discord.Embed(description="Missing required permission `Administrator`.", color=Config.Colours.Negative), ephemeral=True);

    async def OnReady(Discord, Config, Bot, Database):
        for Guild in Bot.guilds:
            CollectedData = Database.execute(f"SELECT MessageId, ChannelId, EndTime FROM Giveaways WHERE GuildId = {Guild.id}").fetchall();
            for Data in CollectedData:
                MessageId = Data[0];
                ChannelId = Data[1];
                EndTime = Data[2];
                Channel = Bot.get_channel(ChannelId);
                PartialMessage = Bot.get_partial_messageable(ChannelId);

                try:
                    Message = await PartialMessage.fetch_message(MessageId);

                    ToMentionQuery = Database.execute(f"SELECT UserMention FROM GiveawayMentions WHERE MessageId = {MessageId}").fetchall();
                    class FakeButton():
                        ToMention = [Gathered[0] for Gathered in ToMentionQuery];

                    await Bot.loop.create_task(GiveawayBackgroundTask(EndTime, Channel, Message, FakeButton, Guild.id));
                except Discord.errors.NotFound:
                    Database.execute(f"DELETE FROM GiveawayMentions WHERE MessageId = {MessageId}");
                    Database.execute(f"DELETE FROM Giveaways WHERE MessageId = {MessageId} AND GuildId = {Guild.id}");
                    Database.commit();

    return OnReady;