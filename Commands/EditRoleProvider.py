Name = "Edit Role Provider";
HelpString = "Run `/editroleprovider` and follow the on-screen instructions to edit an existing role provider menu.";
Description = "Allows you to modifiy a created role provider.";

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

            self.RolegiverTitle = Discord.ui.InputText(label="Role Provider Title", placeholder="Example Role Provider", style=Discord.InputTextStyle.short, max_length=100);
            self.RolenamesAdd = Discord.ui.InputText(label="Roles To Add (Seperate with a comma)", placeholder="Dodge", style=Discord.InputTextStyle.long, required=False);
            self.RolenamesRemove = Discord.ui.InputText(label="Roles To Remove (Seperate with a comma)", placeholder="Dodge", style=Discord.InputTextStyle.long, required=False);

            self.add_item(self.RolegiverTitle);
            self.add_item(self.RolenamesAdd);
            self.add_item(self.RolenamesRemove);

        async def callback(self, interaction):
            Title = self.RolegiverTitle.value.strip();

            RolesToRemove = (self.RolenamesRemove.value or "").strip();
            RolesToRemove = RolesToRemove.split(",");
            RolesToRemove = list(filter(None, RolesToRemove));

            RolesToAdd = (self.RolenamesAdd.value or "").strip();
            RolesToAdd = RolesToAdd.split(",");
            RolesToAdd = list(filter(None, RolesToAdd));

            Rolenames = RolesToRemove + RolesToAdd;

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
                    Embed = Discord.Embed(description=f"Cannot edit role provider with duplicate role `{Rolename}`.", color=Config.Colours.Negative);
                    try: await interaction.response.send_message(embed=Embed, ephemeral=True);
                    except: pass;
                    CanContinue = False;       

            if Database.execute(f"SELECT Title FROM RoleProviders WHERE Title = '{Title}' AND ChannelId = {interaction.channel.id} AND GuildId = {interaction.guild.id}").fetchall() == 0:
                Embed = Discord.Embed(description=f"A roleprovider with the title {Title} does not exists.", color=Config.Colours.Negative);
                try: await interaction.response.send_message(embed=Embed, ephemeral=True);
                except: pass;
                CanContinue = False;    

            if CanContinue:
                RoleproviderMessageId = Database.execute(f"SELECT MessageId FROM RoleProviders WHERE ChannelId = {interaction.channel.id} AND GuildId = {interaction.guild.id} AND Title = '{Title}'").fetchall()[0][0];
                PartialMessage = Bot.get_partial_messageable(interaction.channel.id);

                Rolenames = [];
                Message = await PartialMessage.fetch_message(RoleproviderMessageId);
                for Button in Message.components[0].children:
                    if Button.label not in RolesToRemove:
                        Rolenames.append(Button.label);

                Rolenames += RolesToAdd;

                import copy;

                View = Discord.ui.View(timeout=None);

                for Rolename in Rolenames:
                    Rolename = Rolename.strip();
                    Button = RoleProviderButton(Rolename);
                    View.add_item(Button);

                NewEmbed = copy.copy(Message.embeds[0]);

                await Message.edit(embed=NewEmbed, view=View);

                Description = f"Successfully edited role provider `{Title}`.";
                if len(RolesToAdd) > 0:
                    Description += f"\nRoles added: {', '.join([f'`{Role}`' for Role in RolesToAdd])}.";

                if len(RolesToRemove) > 0:
                    Description += f"\nRoles removed: {', '.join([f'`{Role}`' for Role in RolesToRemove])}.";

                await interaction.response.send_message(embed=Discord.Embed(description=Description, color=Config.Colours.Positive), ephemeral=True);

    @Bot.slash_command(description=Description)
    async def editroleprovider(context):
        if context.author.guild_permissions.administrator:
            if len(Database.execute(f"SELECT MessageId FROM RoleProviders WHERE GuildId = {context.guild.id}").fetchall()) > 0:
                Modal = RoleProviderModal(title="Edit Role Provider", roles=context.guild.roles);
                await context.interaction.response.send_modal(modal=Modal);
            else:
                await context.interaction.response.send_message(embed=Discord.Embed(description="This guild has no active role providers.", color=Config.Colours.Negative), ephemeral=True);
        else:
            await context.interaction.response.send_message(embed=Discord.Embed(description="Missing required permission `Administrator`.", color=Config.Colours.Negative), ephemeral=True);