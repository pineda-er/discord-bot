import asyncio
import os
import discord
from discord.ext import commands

# Set up intents
intents = discord.Intents.all()
intents.members = True

# Create a bot instance with a command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('We Have logged in as {0.user}'.format(bot))
    
@bot.event
async def on_command_error(ctx, error):   
    if isinstance(error, commands.MissingRequiredArgument):
        print(error)

# Asynchronous function to load all cogs (extensions) from the 'cogs' directory
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Main asynchronous function to load cogs and start the bot
async def main():
    await load()
    await bot.start(os.getenv('DISCORD_API_TOKEN'))

# Run the main function
asyncio.run(main())
