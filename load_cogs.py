import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from firebase_config import firebase_config
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from pretty_help import EmojiMenu, PrettyHelp

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {
    'storageBucket' : 'discordbot-1113e.appspot.com'
})


# Set up intents
intents = discord.Intents.all()
intents.members = True

# Create a bot instance with a command prefix and intents
bot = commands.Bot(command_prefix="$", intents=intents)

bot.help_command = PrettyHelp(ephemeral=True, color=discord.Colour.green()) 

@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    await bot.tree.sync()
    
@bot.event
async def on_command_error(ctx, error):   
    if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
        print(error)
        
    
# @bot.hybrid_command()
# async def pong(ctx):
#     await ctx.send("🏓 **Ping!**")
        
# @bot.tree.command(description="hello in another language")
# async def ciao(interaction: discord.Interaction):
#     await interaction.response.send_message(f"Ciao! {interaction.user.mention}", ephemeral=True)

# Asynchronous function to load all cogs (extensions) from the 'cogs' directory
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Main asynchronous function to load cogs and start the bot
async def main():
    await load()
    load_dotenv()
    await bot.start(os.getenv('DISCORD_API_TOKEN'))

# Run the main function
asyncio.run(main())
