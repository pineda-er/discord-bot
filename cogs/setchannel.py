import discord
from discord.ext import commands
from firebase_admin import firestore
db = firestore.client()


# Define a cog class that inherits from commands.Cog
class SetChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_any_role('Admin','Moderator')
    async def setchannel(self, ctx, sub_command : str, channel : discord.TextChannel | str):
        
        if isinstance(channel, discord.TextChannel):
            channel = str(channel.id)
            
        if(sub_command in ("drop","welcome","goodbye")):
            
            #Connects to firebase firestore to set channel
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_server.set({f"{sub_command}_channel" : channel}, merge=True)
            embed = discord.Embed(
                description=f"**Successfully set channel for {sub_command}**",
                colour= 0x008000
            )
            await ctx.send(embed=embed)
    
    @setchannel.error
    async def setup_error(self, ctx, error):
        if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
            embed = discord.Embed(
                title="Invalid arguments",
                description="```SUBCOMMANDS: \n drop \n welcome \n goodbye \n \n ex. \n $setup SUB_COMMAND CHANNEL_ID \n $setup SUB_COMMAND #CHANNEL_NAME```"
            )
            
            await ctx.send(embed=embed)

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(SetChannel(bot))