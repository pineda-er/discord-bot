import asyncio
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from firebase_config import firebase_config
import firebase_admin
from firebase_admin import credentials, firestore, storage
from pretty_help import PrettyHelp
from datetime import timedelta, datetime
import pytz

# Initialize Firebase
cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {'storageBucket': 'discordbot-1113e.appspot.com'})
db = firestore.client()
bucket = storage.bucket()

# Set up intents and bot instance
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)
bot.help_command = PrettyHelp(ephemeral=True, color=discord.Colour.green())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    remove_ex_convict.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
        print(error)

@bot.event
async def on_member_update(before, after):
    your_server = bot.get_guild(before.guild.id)
    # print(f'before {before.roles}')
    # print(f'after {after.roles}')
    await handle_server_booster(before, after, your_server)
    await handle_jail_inmate(before, after, your_server)
    await handle_ex_convict(before, after, your_server)
    await handle_moon_shards(before, after, your_server)

async def handle_server_booster(before, after, server):
    if 'Server Booster' in str(after.roles):
        # print('inside')
        if 'Server Booster' not in str(before.roles):
            # print('inside2')
            await after.add_roles(discord.utils.get(server.roles, name="Server VIP"))
            print(f'INFO: {after.name} has boosted the server')
    elif 'Server Booster' in str(before.roles):
        if 'Server Booster' not in str(after.roles):
            await after.remove_roles(discord.utils.get(server.roles, name="Server VIP"))
            role_ids = [1226865689755648000, 1226866368201363587, 1226866556823277608, 1226866752516784128, 1226866842417758238]
            roles = [discord.utils.get(server.roles, id=n) for n in role_ids]
            await after.remove_roles(*roles)
            print(f'INFO: {after.name} has stopped boosting the server')

async def handle_jail_inmate(before, after, server):
    if 'Jail Inmate' in str(before.roles):
        if 'Jail Inmate' not in str(after.roles):
            await after.add_roles(discord.utils.get(server.roles, name="Ex-Convict"))

async def handle_ex_convict(before, after, server):
    if 'Ex-Convict' in str(after.roles):
        if 'Ex-Convict' not in str(before.roles):
            print(f'INFO: {after.name} became an ex-convict')
            end_date = datetime.now().astimezone(pytz.timezone('Asia/Manila')) + timedelta(days=3)
            db.collection("servers").document(str(before.guild.id)).collection("ex_convict").document(str(before.id)).set({
                "name": after.name, "mention": after.mention, "convict_until": end_date, "guild_id": str(before.guild.id)
            }, merge=True)
    elif 'Ex-Convict' in str(before.roles):
        if 'Ex-Convict' not in str(after.roles):
            # await after.add_roles(discord.utils.get(server.roles, name="Ex-Convict"))
            print(f'INFO: {after.name} has been removed as ex-convict')
            db.collection("servers").document(str(before.guild.id)).collection("ex_convict").document(str(before.id)).delete()

async def handle_moon_shards(before, after, server):
    if '100 Moon Shards' in str(after.roles):
        # print('inside')
        if '100 Moon Shards' not in str(before.roles):
            # print('inside2')
            await after.remove_roles(discord.utils.get(server.roles, name="100 Moon Shards"))
            db_server = db.collection("servers").document(str(before.guild.id))
            db_data = db_server.get().to_dict()
            db_currency = db_server.collection("currency").document(str(before.id))
            db_currency_receiver = db_currency.get().to_dict()
            db_currency.update({"balance": db_currency_receiver["balance"] + 100})
            db_server.set({"total_moonshards": db_data["total_moonshards"] + 100}, merge=True)
            print(f'INFO: {after.name} got 100 Moon Shards')

@tasks.loop(hours=1, reconnect=True)
async def remove_ex_convict():
    # print("Checking...")
    db_server = db.collection("servers").document("1199642321109663754")
    db_ex_convicts = db_server.collection("ex_convict").stream()
    # print("seees")
    for doc in db_ex_convicts:
        # print(doc.id)
        ex_convict = doc.to_dict()
        # print(ex_convicts)
        # end_date = datetime.fromtimestamp(ex_convicts["convict_until"].timestamp())
        # print(end_date)
        # print(ex_convicts["convict_until"].timestamp())
        end_date = int(ex_convict["convict_until"].timestamp())
        date_now = int(datetime.now().astimezone(pytz.timezone('Asia/Manila')).timestamp())
        # print(f'{end_date} > {date_now}')
        # print(ex_convicts["guild_id"])
        # guild = bot.get_guild(int(ex_convicts["guild_id"]))
        # print(str(guild.roles))
        if end_date > date_now:
            continue
        # print(ex_convicts["guild_id"])
        guild = bot.get_guild(int(ex_convict["guild_id"]))
        # print(guild.roles)
        role = discord.utils.get(guild.roles, name="Ex-Convict") if guild else None
        if guild and role:
            member = discord.utils.get(guild.members, name=ex_convict["name"])
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
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Main asynchronous function to load cogs and start the bot
async def main():
    await load_cogs()
    load_dotenv()
    await bot.start(os.getenv('DISCORD_API_TOKEN'))

# Run the main function
asyncio.run(main())