Name = "New Role Provider";
HelpString = "Run `/newroleprovider` and follow the on-screen instructions to create a role provider menu.";
Description = "Creates a menu that allows users to self-assign roles.";

def Init(Discord, Config, Bot, Database):
    class RoleProviderButton(Discord.ui.Button):
        def __init__(self, label):
            super().__init__(label=label, custom_id=f"'{label}UUID'", style=Discord.ButtonStyle.primary);

        async def callback(self, interaction):
            Role = Discord.utils.get(interaction.guild.roles, name=self.label);
            if Role in interaction.user.roles: 
                await interaction.user.remove_roles(Role);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully removed role `{self.label}`.", color=Config.Colours.Positive), ephemeral=True);
            else: 
                await interaction.user.add_roles(Role);
                await interaction.response.send_message(embed=Discord.Embed(description=f"Successfully added role `{self.label}`.", color=Config.Colours.Positive), ephemeral=True);

    class RoleProviderModal(Discord.ui.Modal):
        def __init__(self, title, roles):
            super().__init__(title=title);

            self.RolegiverTitle = Discord.ui.InputText(label="Role Provider Title (Must be unique)", placeholder="Example Role Provider", style=Discord.InputTextStyle.short, max_length=100);
            self.RolenamesInput = Discord.ui.InputText(label="Roles (Seperate with a comma)", placeholder="Dodge", style=Discord.InputTextStyle.long);

            self.add_item(self.RolegiverTitle);
            self.add_item(self.RolenamesInput);

        async def callback(self, interaction):
            Title = self.RolegiverTitle.value.strip();

            Rolenames = self.RolenamesInput.value.strip();
            Rolenames = Rolenames.split(",");
            Rolenames = list(filter(None, Rolenames));

            CanContinue = True;
            for Rolename in Rolenames:
                Rolename = Rolename.strip();
                if Rolename not in [Role.name for Role in interaction.guild.roles]:
                    Embed = Discord.Embed(description=f"Cannot find role `{Rolename}`.", color=Config.Colours.Negative);
                    try: await interaction.response.send_message(embed=Embed, ephemeral=True);
                    except: pass;
                    CanContinue = False;

            for Rolename in Rolenames:
                if Rolenames.count(Rolename) > 1:
                    Embed = Discord.Embed(description=f"Cannot create role provider with duplicate role `{Rolename}`.", color=Config.Colours.Negative);
                    try: await interaction.response.send_message(embed=Embed, ephemeral=True);
                    except: pass;
                    CanContinue = False;       

            if not Database.execute(f"SELECT Title FROM RoleProviders WHERE Title = '{Title}' AND ChannelId = {interaction.channel.id} AND GuildId = {interaction.guild.id}").fetchall() == 0:
                Embed = Discord.Embed(description=f"A roleprovider with the title {Title} already exists.", color=Config.Colours.Negative);
                try: await interaction.response.send_message(embed=Embed, ephemeral=True);
                except: pass;
                CanContinue = False;       

            if CanContinue:
                View = Discord.ui.View(timeout=None);

                for Rolename in Rolenames:
                    Rolename = Rolename.strip();
                    Button = RoleProviderButton(Rolename);
                    View.add_item(Button);

                Embed = Discord.Embed(title=Title, description=f"Click on the buttons below to get/remove its corresponding role.", color=Config.Colours.Positive);

                Interaction = await interaction.response.send_message(embed=Embed, view=View);
                Message = await Interaction.original_message();

                Database.execute(f"INSERT INTO RoleProviders (MessageId, ChannelId, GuildId, Title) VALUES ({Message.id}, {Message.channel.id}, {Interaction.guild.id}, '{Title}')");
                Database.commit();

    @Bot.slash_command(description=Description)
    async def newroleprovider(context):
        if context.author.guild_permissions.administrator:
            if len(Database.execute(f"SELECT MessageId FROM RoleProviders WHERE GuildId = {context.guild.id}").fetchall()) < 5:
                Modal = RoleProviderModal(title="New Role Provider", roles=context.guild.roles);
                await context.interaction.response.send_modal(modal=Modal);
            else:
                await context.interaction.response.send_message(embed=Discord.Embed(description="This guild already has 5 active role providers.", color=Config.Colours.Negative), ephemeral=True);
        else:
            await context.interaction.response.send_message(embed=Discord.Embed(description="Missing required permission `Administrator`.", color=Config.Colours.Negative), ephemeral=True);

    async def OnReady(Discord, Config, Bot, Database):
        for Guild in Bot.guilds:
            CollectedData = Database.execute(f"SELECT MessageId, ChannelId FROM RoleProviders WHERE GuildId = {Guild.id}").fetchall();
            for Data in CollectedData:
                MessageId = Data[0];
                ChannelId = Data[1];
                Channel = Bot.get_partial_messageable(ChannelId);

                try: 
                    Rolenames = [];
                    Message = await Channel.fetch_message(MessageId);
                    for Button in Message.components[0].children:
                        Rolenames.append(Button.label);

                    import copy;

                    View = Discord.ui.View(timeout=None);

                    for Rolename in Rolenames:
                        Rolename = Rolename.strip();
                        Button = RoleProviderButton(Rolename);
                        View.add_item(Button);

                    NewEmbed = copy.copy(Message.embeds[0]);

                    await Message.edit(embed=NewEmbed, view=View);
                except Discord.errors.NotFound:
                    Database.execute(f"DELETE FROM RoleProviders WHERE GuildId = {Guild.id} AND MessageId = {MessageId} AND ChannelId = {ChannelId}");
                    Database.commit();
    
    return OnReady;
