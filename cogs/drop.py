import os
import discord
from discord.ext import commands

class SimpleView(discord.ui.View):
    
    foo : bool = None
    
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        # await self.message.channel.send("Timedout")
        await self.disable_all_items()
    
    @discord.ui.button(label="💸 Grab", 
                       style=discord.ButtonStyle.success)
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button):
        if(self.foo != True):
            
            await interaction.response.send_message(f"Congratulations {interaction.user.mention}, you got it!")
            self.foo = True
            # self.stop()
        else:
            await interaction.response.send_message("Sorry! You were too late!", ephemeral=True)
            self.stop
            
    
    # @hello.error
    # async def say_error(self, interaction: discord.Interaction):
        # await interaction.response.send_message("Sorry!")
    #     self.stop()

# Define a cog class that inherits from commands.Cog
class drop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event listener for when the bot is ready
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     print(f'Logged in as {self.bot.user.name}')

    # Command that responds with "Pong" when the bot receives a "!ping" command
    @commands.command()
    async def drop(self, ctx, amount= None):
        if(amount == "50" or amount == "100" or amount == "nitro"):
            channel = self.bot.get_channel(int(os.environ['DROP_CHANNEL']))
            file = discord.File(f'./image/{amount}.jpg')
            embed = discord.Embed()
            embed.set_image(url=f"attachment://{amount}.jpg")
            embed.set_footer(text="Grab it before someone else does!")
            view = SimpleView(timeout=2)
            
            message = await channel.send('**Hala nahulog!**', embed=embed, file=file, view=view)
            # message = await channel.send(view=view)
            view.message = message
            
            await view.wait()
            await view.disable_all_items()
        
        elif(amount is None):
            await ctx.send('input `50` or `100`')
    @drop.error
    async def say_error(ctx, error):
        if isinstance(error, commands.CommandError):
                print(error)

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(drop(bot))