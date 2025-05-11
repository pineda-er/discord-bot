import discord
from discord.ext import commands
from discord import app_commands
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
from datetime import timedelta, datetime as datetimes
db = firestore.client()
from typing import Callable, Optional, List
import pytz


class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def navigate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        if self.index > self.total_pages // 2:
            self.children[2].emoji = "⏮️"
        else:
            self.children[2].emoji = "⏭️"
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.index <= self.total_pages//2:
            self.index = self.total_pages
        else:
            self.index = 1
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1


# Define a cog class that inherits from commands.Cog
class Monitor(commands.Cog):
    
    """commands: monitor"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Monitor ready")
        
    
    @app_commands.command(name="monitor_check", description="Check ex-convict list/status")
    async def monitor_check(self, interaction: discord.Interaction):
        items = []
        
        try:
            from strings import DIGITAL_ONE_GUILD_ID
            db_server = db.collection("servers").document(str(DIGITAL_ONE_GUILD_ID))
            db_ex_convicts = db_server.collection("ex_convict").stream()
            
            for doc in db_ex_convicts:
                ex_convicts = doc.to_dict()
                date = int(ex_convicts["convict_until"].timestamp())
                items.append(f'{ex_convicts["mention"]} \n Until: <t:{str(date)}:f>')
            
            if not items:
                items.append('No ex-convicts found.')
            
            nameslist = '\n \n '.join(sorted(items))
            users = items
            
            L = 5  # elements per page
            async def get_page(page: int):
                emb = discord.Embed(title="Ex-Convict List", description="")
                offset = (page - 1) * L
                for user in users[offset:offset + L]:
                    emb.description += f"{user}\n \n"
                n = Pagination.compute_total_pages(len(users), L)
                emb.set_footer(text=f"Page {page} from {n}")
                return emb, n

            await Pagination(interaction, get_page).navigate()
        
        except Exception as e:
            embed = discord.Embed(
                colour=0xff2c2c,
                title="Error",
                description=f"An error occurred while fetching the ex-convict list: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="monitor_check_member", description="Check ex-convict list/status")
    async def monitor_check_member(self, interaction: discord.Interaction, member: discord.Member):
        items = []
        from strings import DIGITAL_ONE_GUILD_ID
        db_server = db.collection("servers").document(str(DIGITAL_ONE_GUILD_ID))
        db_ex_convicts = db_server.collection("ex_convict")
        db_ex_convicts = db_ex_convicts.where(filter=FieldFilter("name", "==", member.name)).stream()
        
        for doc in db_ex_convicts:
            ex_convicts = doc.to_dict()
            date = datetime.datetime.fromtimestamp(ex_convicts["convict_until"].timestamp())
            date = int(ex_convicts["convict_until"].timestamp())
            items.append(f'{ex_convicts["mention"]} \n Until: <t:{str(date)}:f>')
        
        if not items:
            items.append('Member not found in Ex-Convict List')
            title = 'Member not found'
        else:
            title = 'Ex-Convict List'
            
        nameslist = '\n \n '.join(sorted(items))
            
        embed = discord.Embed(
            colour=0x6ac5fe,
            title= title
        )
        embed.add_field(name = ' ', value = nameslist)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="monitor_remove_member", description="remove member from ex-convict list")
    @app_commands.checks.has_any_role("Admin", "Moderator", "Staff")
    async def monitor_remove_member(self, interaction: discord.Interaction, member: discord.Member):
        try:
            ex_convict_role = discord.utils.get(interaction.guild.roles, name="Ex-Convict")
            if not ex_convict_role:
                raise ValueError('The "Ex-Convict" role does not exist in this server.')

            if ex_convict_role in member.roles:
                await member.remove_roles(ex_convict_role)
                embed = discord.Embed(
                    colour=0x6ac5fe,
                    title='Member removed',
                    description=f'{member.mention} has been removed as Ex-Convict'
                )
            else:
                embed = discord.Embed(
                    colour=0xff2c2c,
                    title='Error',
                    description=f'{member.mention} does not have the "Ex-Convict" role.'
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    colour=0xff2c2c,
                    title="Error",
                    description=f"An error occurred: {str(e)}"
                ),
                ephemeral=True
            )

    @app_commands.command(name="monitor_remove_expired_members", description="remove members from ex-convict list")
    @app_commands.checks.has_any_role("Admin", "Moderator", "Staff")
    async def monitor_remove_expired_members(self, interaction: discord.Interaction):
        try:
            items = 0
            date_now = datetimes.now().astimezone(pytz.timezone('Asia/Manila'))
            date_now = int(datetimes.timestamp(date_now))

            from strings import DIGITAL_ONE_GUILD_ID
            db_server = db.collection("servers").document(str(DIGITAL_ONE_GUILD_ID))
            db_ex_convicts = db_server.collection("ex_convict").stream()

            for doc in db_ex_convicts:
                ex_convicts = doc.to_dict()
                end_date = int(ex_convicts["convict_until"].timestamp())
                if end_date < date_now:
                    member = discord.utils.get(interaction.guild.members, name=ex_convicts["name"])
                    if member:
                        ex_convict_role = discord.utils.get(interaction.guild.roles, name="Ex-Convict")
                        if ex_convict_role:
                            await member.remove_roles(ex_convict_role)
                    db_server.collection("ex_convict").document(str(doc.id)).delete()
                    items += 1

            embed = discord.Embed(
                colour=0x6ac5fe,
                title='Members removed',
                description=f'{items} members have been removed as Ex-Convict'
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    colour=0xff2c2c,
                    title="Error",
                    description=f"An error occurred: {str(e)}"
                ),
                ephemeral=True
            )

    @app_commands.command(name="monitor_add_member", description="add member to ex-convict list")
    @app_commands.checks.has_any_role("Admin", "Moderator", "Staff")
    async def monitor_add_member(self, interaction: discord.Interaction, member: discord.Member):
        try:
            ex_convict_role = discord.utils.get(interaction.guild.roles, name="Ex-Convict")
            if not ex_convict_role:
                raise ValueError('The "Ex-Convict" role does not exist in this server.')

            if ex_convict_role not in member.roles:
                await member.add_roles(ex_convict_role)
                embed = discord.Embed(
                    colour=0x6ac5fe,
                    title='Member added',
                    description=f'{member.mention} has been added as Ex-Convict'
                )
            else:
                embed = discord.Embed(
                    colour=0xff2c2c,
                    title='Error',
                    description=f'{member.mention} already has the "Ex-Convict" role.'
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    colour=0xff2c2c,
                    title="Error",
                    description=f"An error occurred: {str(e)}"
                ),
                ephemeral=True
            )

    @app_commands.command(name="monitor_remove_multiple_members", description="Remove multiple members from the ex-convict list")
    @app_commands.checks.has_any_role("Admin", "Moderator", "Staff")
    async def monitor_remove_multiple_members(self, interaction: discord.Interaction, members: str):
        """
        Removes multiple members from the ex-convict list.
        :param members: A string of member mentions (e.g., "@User1 @User2").
        """
        try:
            ex_convict_role = discord.utils.get(interaction.guild.roles, name="Ex-Convict")
            if not ex_convict_role:
                raise ValueError('The "Ex-Convict" role does not exist in this server.')

            # Parse member mentions from the input string
            member_ids = [int(mention.strip("<@!>")) for mention in members.split() if mention.startswith("<@")]
            removed_members = []

            for member_id in member_ids:
                member = interaction.guild.get_member(member_id)
                if member and ex_convict_role in member.roles:
                    await member.remove_roles(ex_convict_role)
                    removed_members.append(member.mention)

            if removed_members:
                embed = discord.Embed(
                    colour=0x6ac5fe,
                    title='Members removed',
                    description=f'The following members have been removed as Ex-Convict:\n' + '\n'.join(removed_members)
                )
            else:
                embed = discord.Embed(
                    colour=0xff2c2c,
                    title='No members removed',
                    description='None of the specified members had the "Ex-Convict" role or were invalid.'
                )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    colour=0xff2c2c,
                    title="Error",
                    description=f"An error occurred: {str(e)}"
                ),
                ephemeral=True
            )
        

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Monitor(bot))