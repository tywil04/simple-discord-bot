Name = "New Countdown";
HelpString = "Run `/newcountdown` and follow the on-screen instructions. This will create a countdown that allows users to get notified when the countdown ends.";
Description = "Creates a countdown that notifies users when finished."

import asyncio
import time;
import copy;

def Init(Discord, Config, Bot, Database):
    async def CountdownBackgroundTask(EndTime, SendObject, Message, NotificationButton, GuildId):
        if EndTime <= time.time():
            NewEmbed = copy.copy(Message.embeds[0]);
            NewEmbed.description = f"Countdown over!";

            await Message.edit(embed=NewEmbed, view=None);
            await SendObject.send(content=", ".join(NotificationButton.ToMention), embed=Discord.Embed(
                description=f"The countdown `{NewEmbed.title}` has finished.",
                color=Config.Colours.Positive,
            ));

            Database.execute(f"DELETE FROM Countdowns WHERE MessageId = {Message.id} AND GuildId = {GuildId}");
            Database.execute(f"DELETE FROM CountdownMentions WHERE MessageId = {Message.id}");
            Database.commit();
        else:
            Minutes, Seconds = divmod(EndTime - time.time(), 60)
            Hours, Minutes = divmod(Minutes, 60)
            Days, Hours = divmod(Hours, 24)

            NewEmbed = copy.copy(Message.embeds[0]);
            NewEmbed.description = f"Use the `Get Notified` button below to get/remove a notification when the countdown ends.\n\nTime remaining:\nDay(s): **{int(Days)}**\nHour(s): **{int(Hours)}**\nMinute(s): **{int(Minutes)}**";

            NewView = Discord.ui.View(timeout=None);
            NewButton = CountdownButton(label=Message.components[0].children[0].label, countdownname=NewEmbed.title, tomention=NotificationButton.ToMention);
            NewView.add_item(NewButton);

            if NewEmbed.description != Message.embeds[0].description:
                await Message.edit(embed=NewEmbed, view=NewView);

            await asyncio.sleep(15);

            Bot.loop.create_task(CountdownBackgroundTask(EndTime, SendObject, Message, NewButton, GuildId));

    class CountdownButton(Discord.ui.Button):
        def __init__(self, label, countdownname, tomention=[]):
            super().__init__(label=label, custom_id=f"'{label}UUID'", style=Discord.ButtonStyle.primary);
            self.ToMention = tomention;
            self.CountdownName = countdownname;

        async def callback(self, interaction):
            if interaction.user.mention in self.ToMention:
                self.ToMention.remove(interaction.user.mention);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully removed you from the notification list for countdown `{self.CountdownName}`", color=Config.Colours.Positive), ephemeral=True);
                Database.execute(f"DELETE FROM CountdownMentions WHERE MessageId = {interaction.message.id} AND UserMention = '{interaction.user.mention}'");
                Database.commit();
            else:
                self.ToMention.append(interaction.user.mention);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully added you to the notification list for countdown `{self.CountdownName}`.", color=Config.Colours.Positive), ephemeral=True);
                if not interaction.user.mention in [UserMention[0] for UserMention in Database.execute(f"SELECT UserMention FROM CountdownMentions WHERE MessageId = {interaction.message.id}").fetchall()]:
                    Database.execute(f"INSERT INTO CountdownMentions (MessageId, UserMention) VALUES ({interaction.message.id}, '{interaction.user.mention}')");
                    Database.commit();

    class CountdownModal(Discord.ui.Modal):
        def __init__(self, title):
            super().__init__(title=title);

            self.CountdownTitle = Discord.ui.InputText(label="Countdown Title", placeholder="Example Countdown", style=Discord.InputTextStyle.short, max_length=100);
            self.CountdownDays = Discord.ui.InputText(label="Days until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);
            self.CountdownHours = Discord.ui.InputText(label="Hours until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);
            self.CountdownMinutes = Discord.ui.InputText(label="Minutes until end (Leave blank for 0)", required=False, style=Discord.InputTextStyle.short);

            self.add_item(self.CountdownTitle);
            self.add_item(self.CountdownDays);
            self.add_item(self.CountdownHours);
            self.add_item(self.CountdownMinutes);

        async def callback(self, interaction):
            try:
                Minutes = int(self.CountdownMinutes.value or 0);
                Hours = int(self.CountdownHours.value or 0);
                Days = int(self.CountdownDays.value or 0);

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

                    NotificationSubscribeButton = CountdownButton(label="Get Notified", countdownname=self.CountdownTitle.value.strip());
                    View = Discord.ui.View(NotificationSubscribeButton, timeout=None);
                    Embed = Discord.Embed(title=self.CountdownTitle.value.strip(), description=f"Use the `Get Notified` button below to get/remove a notification when the countdown ends.\n\nTime remaining:\nDay(s): **{int(Days)}**\nHour(s): **{int(Hours)}**\nMinute(s): **{int(Minutes)}**", color=Config.Colours.Positive);
                    Countdown = await interaction.response.send_message(embed=Embed, view=View);
                    CountdownMessage = await Countdown.original_message();

                    Database.execute(f"INSERT INTO Countdowns (MessageId, ChannelId, GuildId, EndTime) VALUES ({CountdownMessage.id}, {CountdownMessage.channel.id}, {interaction.guild.id}, {EndTime})");
                    Database.commit();

                    Bot.loop.create_task(CountdownBackgroundTask(EndTime, interaction.followup, CountdownMessage, NotificationSubscribeButton, interaction.guild.id));
            except: await interaction.response.send_message(embed=Discord.Embed(description="Error when parsing provided time. Did you include any non-digit characters?", color=Config.Colours.Negative), ephemeral=True);

    @Bot.slash_command(description=Description)
    async def newcountdown(context):
        if context.author.guild_permissions.administrator:
            if len(Database.execute(f"SELECT MessageId FROM Countdowns WHERE GuildId = {context.guild.id}").fetchall()) < 5:
                Modal = CountdownModal(title="New Countdown");
                await context.interaction.response.send_modal(Modal);
            else:
                await context.interaction.response.send_message(embed=Discord.Embed(description="This guild already has `5` active countdowns.", color=Config.Colours.Negative), ephemeral=True);
        else:
            await context.interaction.response.send_message(embed=Discord.Embed(description="Missing required permission `Administrator`.", color=Config.Colours.Negative), ephemeral=True);

    async def OnReady(Discord, Config, Bot, Database):
        for Guild in Bot.guilds:
            CollectedData = Database.execute(f"SELECT MessageId, ChannelId, EndTime FROM Countdowns WHERE GuildId = {Guild.id}").fetchall();
            for Data in CollectedData:
                MessageId = Data[0];
                ChannelId = Data[1];
                EndTime = Data[2];
                Channel = Bot.get_channel(ChannelId);
                PartialMessage = Bot.get_partial_messageable(ChannelId);

                try:
                    Message = await PartialMessage.fetch_message(MessageId);

                    ToMentionQuery = Database.execute(f"SELECT UserMention FROM CountdownMentions WHERE MessageId = {MessageId}").fetchall();
                    class FakeButton():
                        ToMention = [Gathered[0] for Gathered in ToMentionQuery];

                    await Bot.loop.create_task(CountdownBackgroundTask(EndTime, Channel, Message, FakeButton, Guild.id));
                except Discord.errors.NotFound:
                    Database.execute(f"DELETE FROM CountdownMentions WHERE MessageId = {MessageId}");
                    Database.execute(f"DELETE FROM Countdowns WHERE MessageId = {MessageId} AND GuildId = {Guild.id}");
                    Database.commit();

    return OnReady;