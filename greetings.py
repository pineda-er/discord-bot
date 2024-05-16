import discord
from discord.ext import commands

# Define a cog class that inherits from commands.Cog
class ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event listener for when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online!")

    # Command that responds with "Pong" when the bot receives a "!ping" command
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong")

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(ping(bot))