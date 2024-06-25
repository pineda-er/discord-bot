import discord
from discord.ext import commands
from discord import app_commands
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
db = firestore.client()
from typing import Callable, Optional


class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navegate(self):
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
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_ex_convicts = db_server.collection("ex_convict")
        db_ex_convicts = db_ex_convicts.stream()
        
        for doc in db_ex_convicts:
            # print(doc.id)
            ex_convicts = doc.to_dict()
            # print(ex_convicts)
            date = datetime.datetime.fromtimestamp(ex_convicts["convict_until"].timestamp())
            # print(date)
            # print(ex_convicts["convict_until"].timestamp())
            date = int(ex_convicts["convict_until"].timestamp())
            items.append(f'{ex_convicts["mention"]} \n Until: <t:{str(date)}:f>')
            # print(items)
            
        nameslist = '\n \n '.join(sorted(items))
        users = items
        
        # print(items)
        # print(nameslist)
        # print(users)
        # This is a long list of results
        # I'm going to use pagination to display the data
        L = 5    # elements per page
        async def get_page(page: int):
            emb = discord.Embed(title="Ex-Convict List", description="")
            offset = (page-1) * L
            for user in users[offset:offset+L]:
                emb.description += f"{user}\n \n"
            # emb.set_author(name=f"Requested by {interaction.user}")
            n = Pagination.compute_total_pages(len(users), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n

        await Pagination(interaction, get_page).navegate()
        
    @app_commands.command(name="monitor_check_member", description="Check ex-convict list/status")
    async def monitor_check_member(self, interaction: discord.Interaction, member: discord.Member):
        items = []
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_ex_convicts = db_server.collection("ex_convict")
        db_ex_convicts = db_ex_convicts.where(filter=FieldFilter("name", "==", member.name)).stream()
        
        for doc in db_ex_convicts:
            # print(doc.id)
            ex_convicts = doc.to_dict()
            # print(ex_convicts)
            date = datetime.datetime.fromtimestamp(ex_convicts["convict_until"].timestamp())
            # print(date)
            # print(ex_convicts["convict_until"].timestamp())
            date = int(ex_convicts["convict_until"].timestamp())
            items.append(f'{ex_convicts["mention"]} \n Until: <t:{str(date)}:f>')
            # print(items)
        
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
        
        

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Monitor(bot))