import asyncio
import os
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
from firebase_config import firebase_config
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
from google.cloud.firestore_v1.base_query import FieldFilter
from pretty_help import EmojiMenu, PrettyHelp
from datetime import timedelta, datetime
import pytz

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {
    'storageBucket' : 'discordbot-1113e.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()


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
    remove_ex_convict.start()
    
@bot.event
async def on_command_error(ctx, error):   
    if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
        print(error)
        
@bot.event
async def on_member_update(before, after):
    yourServer = bot.get_guild(int(before.guild.id))
    # print(f'before {before.roles}')
    # print(f'after {after.roles}')
    
    if 'Server Booster' in str(after.roles):
        # print('inside')
        if not 'Server Booster' in str(before.roles):
            # print('inside2')
            await after.add_roles(discord.utils.get(yourServer.roles, name="Server VIP"))
            print(f' INFO: {after.name} has boosted the server')
            
    if 'Server Booster' in str(before.roles):
        if not 'Server Booster' in str(after.roles):
            await after.remove_roles(discord.utils.get(yourServer.roles, name="Server VIP"))
            print(f' INFO: {after.name} has stopped boosting the server')
            
    if 'Jail Inmate' in str(before.roles):
        if not 'Jail Inmate' in str(after.roles):
            await after.add_roles(discord.utils.get(yourServer.roles, name="Ex-Convict"))
            
    if 'Ex-Convict' in str(after.roles):
        if not 'Ex-Convict' in str(before.roles):
            print(f' INFO: {after.name} became an ex-convict')
            end_date = datetime.now()
            end_date = end_date.astimezone(pytz.timezone('Asia/Manila'))
            end_date = end_date + timedelta(days=5)
            # print(end_date)
            
            db_server = db.collection("servers").document(str(before.guild.id))
            db_ex_convicts = db_server.collection("ex_convict").document(str(before.id))
            db_ex_convicts.set({"name" : after.name, "mention": after.mention, "convict_until": end_date, "guild_id": str(before.guild.id)}, merge=True)
            
    if 'Ex-Convict' in str(before.roles):
        if not 'Ex-Convict' in str(after.roles):
            # await after.add_roles(discord.utils.get(yourServer.roles, name="Ex-Convict"))
            print(f' INFO: {after.name} has been removed as ex-convict')
            
            db_server = db.collection("servers").document(str(before.guild.id))
            db_ex_convicts = db_server.collection("ex_convict").document(str(before.id)).delete()
            
@tasks.loop(hours=1)
async def remove_ex_convict():
    # print("hjghjghj")
    items = []
    db_server = db.collection("servers").document(str(1199642321109663754))
    db_ex_convicts = db_server.collection("ex_convict")
    db_ex_convicts = db_ex_convicts.stream()
    
    # print("seees")
    for doc in db_ex_convicts:
        # print(doc.id)
        ex_convicts = doc.to_dict()
        # print(ex_convicts)
        end_date = datetime.fromtimestamp(ex_convicts["convict_until"].timestamp())
        # print(end_date)
        # print(ex_convicts["convict_until"].timestamp())
        end_date = int(ex_convicts["convict_until"].timestamp())
        date_now = datetime.now()
        date_now = int(datetime.timestamp(date_now))
        # print(f'{end_date} > {date_now}')
        # print(ex_convicts["guild_id"])
        # guild = bot.get_guild(int(ex_convicts["guild_id"]))
        # print(str(guild.roles))
        
        
        if end_date > date_now: continue
        # print(ex_convicts["guild_id"])
        guild = bot.get_guild(int(ex_convicts["guild_id"]))
        # print(guild.roles)
        role = discord.utils.get(guild.roles, name="Ex-Convict") if guild else None
        if guild and role:
            member = discord.utils.get(guild.members, name=ex_convicts["name"])
            await member.remove_roles(role)
        
        
        
        
        
        
        # items.append(f'{ex_convicts["mention"]} \n Until: <t:{str(date)}:f>')
        # print(items)
            
        
     
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
