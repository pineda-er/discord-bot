import discord
from discord.ext import commands
from firebase_admin import firestore
db = firestore.client()

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
            await interaction.response.send_message("Sorry! this was already grabbed", ephemeral=True)
            self.stop
            
    
    # @hello.error
    # async def say_error(self, interaction: discord.Interaction):
        # await interaction.response.send_message("Sorry!")
    #     self.stop()

# Define a cog class that inherits from commands.Cog
class drop(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_any_role('Admin','Moderator')
    async def drop(self, ctx, amount = None):
        if(amount in ("50","100","nitro")):
            
            #Connects to firebase firestore to get channel
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_channel = db_server.get().to_dict()
            db_channel = db_channel["drop_channel"]
            
            channel = self.bot.get_channel(int(db_channel))
            file = discord.File(f'./image/{amount}.jpg')
            embed = discord.Embed(
                title=f"Someone dropped a {amount}!"
            )
            embed.set_image(url=f"attachment://{amount}.jpg")
            embed.set_footer(text="Grab it!")
            view = SimpleView(timeout=10)
            
            message = await channel.send('**Hala nahulog!**', embed=embed, file=file, view=view)
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