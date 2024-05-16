import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Set up intents
intents = discord.Intents.all()
intents.members = True

# Create a bot instance with a command prefix and intents
bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('We Have logged in as {0.user}'.format(bot))
    await bot.tree.sync()
    
@bot.event
async def on_command_error(ctx, error):   
    if isinstance(error, commands.MissingRequiredArgument):
        print(error)
        
    
@bot.hybrid_command()
async def pong(ctx):
    await ctx.send("🏓 **Ping!**")
        
@bot.tree.command(description="hello in another language")
async def ciao(interaction: discord.Interaction):
    await interaction.response.send_message(f"Ciao! {interaction.user.mention}", ephemeral=True)

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
