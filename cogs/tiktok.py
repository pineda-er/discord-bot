import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from utils import *
from strings import *
import io
from datetime import datetime, timedelta, timezone

db = firestore.client()

class TikTok(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tiktrack", description="Monitor or scrape TikTok user videos.")
    @app_commands.describe(
        option="Choose 'monitor' to monitor a user, 'scrape' to scrape now, or 'list' to list monitored users.",
        username="Username to monitor or scrape (do not include the @ symbol)"
    )
    @app_commands.choices(option=[
        app_commands.Choice(name="Monitor", value="monitor"),
        app_commands.Choice(name="Monitor list", value="list"),
        app_commands.Choice(name="Scrape", value="scrape"),
        app_commands.Choice(name="Archive", value="archive"),
    ])
    async def tiktrack(self, interaction: discord.Interaction, option: app_commands.Choice[str], username: str = None):
        db_server = get_db_server()
        if option.value == "monitor":
            if not username:
                embed = create_embed(description=f"{WARNING_ICON} You must provide a TikTok username to monitor.", colour=0xffd700)
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return
            # Remove '@' if present in username
            if username.startswith("@"): 
                username = username[1:]
            # Also handle accidental '@' anywhere in the username
            username = username.replace("@", "")
            coins = 5
            # Check if user has at least 5 coins in their balance before proceeding
            db_currency = get_db_currency(db_server)
            user_currency_doc = db_currency.document(str(interaction.user.id)).get()
            user_currency = user_currency_doc.to_dict() if user_currency_doc.exists else None
            if not user_currency or user_currency.get("balance", 0) < 5:
                embed = create_embed(description=f"**{WARNING_ICON} You need at least {coins} Coins to monitor a TikTok user.**\n\nGet coins [here](<https://ptb.discord.com/channels/1369536478278975530/shop/1371434524860219555>) or use `/buy`", colour=0xffd700)
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return
            embed = create_embed(description=f"{SEARCH_ICON} Searching for TikTok user `{username}`...", colour=0x6ac5fe)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            try:
                if not db_server:
                    embed = create_embed(description=f"{DATABASE_ICON} Database connection failed.", colour=0xff2c2c)
                    await interaction.edit_original_response(embed=embed)
                    return
                db_tiktok = db_server.collection("tiktok")
                # Check if username is already being monitored by this user
                try:
                    user_doc = db_tiktok.document(str(interaction.user.id)).collection("monitor").where(filter=FieldFilter("username", "==", username)).stream()
                except Exception as e:
                    embed = create_embed(description=f"{DATABASE_ICON} Database error: {e}", colour=0xff2c2c)
                    await interaction.edit_original_response(embed=embed)
                    return
                if any(True for _ in user_doc):
                    embed = create_embed(description=f"{WARNING_ICON} You are already monitoring TikTok user `{username}`.", colour=0xffd700)
                    await interaction.edit_original_response(embed=embed)
                    return
                result = await self.start_monitoring(username)
                if result and result.get('success'):
                    sec_uid = result['sec_uid']
                    video_id = result['video_id']
                    create_time = result['create_time']
                    guild = interaction.guild
                    if not guild:
                        embed = create_embed(description="Guild not found.", colour=0xff2c2c)
                        await interaction.edit_original_response(embed=embed)
                        return
                    category_name = interaction.user.name
                    channel_name = "tiktrack-monitor"
                    # Check or create category and channel
                    category = discord.utils.get(guild.categories, name=category_name)
                    if not category:
                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(view_channel=False),
                            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
                        }
                        try:
                            category = await guild.create_category(name=category_name, reason="TikTok monitor setup", overwrites=overwrites)
                        except Exception as e:
                            embed = create_embed(description=f"{ERROR_ICON} Failed to create category: {e}", colour=0xff2c2c)
                            await interaction.edit_original_response(embed=embed)
                            return
                    channel = discord.utils.get(category.channels, name=channel_name)
                    if not channel:
                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(view_channel=False),
                            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
                        }
                        try:
                            channel = await guild.create_text_channel(name=channel_name, category=category, reason="TikTok monitor setup", overwrites=overwrites)
                        except Exception as e:
                            embed = create_embed(description=f"{ERROR_ICON} Failed to create channel: {e}", colour=0xff2c2c)
                            await interaction.edit_original_response(embed=embed)
                            return
                    tiktok_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                    try:
                        file = await download_tiktok_video(video_id, tiktok_url)
                    except Exception as e:
                        embed = create_embed(description=f"{ERROR_ICON} Failed to download TikTok video: {e}", colour=0xff2c2c)
                        await interaction.edit_original_response(embed=embed)
                        return
                    try:
                        await channel.send(content=f"Latest video from `{username}`:\n[[Link]](<{tiktok_url}>) ||{interaction.user.mention}||", file=file)
                    except Exception as e:
                        embed = create_embed(description=f"{ERROR_ICON} Failed to send video to channel: {e}", colour=0xff2c2c)
                        await interaction.edit_original_response(embed=embed)
                        return
                    msg = f"**{SUCCESS_ICON} Monitoring TikTok user `{username}` every 1 hour.**\n\n{COINS_JUMP_ICON}**{coins}** Coins have been deducted from your balance."
                    try:
                        db_tiktok.document(str(interaction.user.id)).set({"mention": interaction.user.mention, "userID": interaction.user.id}, merge=True)
                        db_tiktok.document(str(interaction.user.id)).collection("monitor").document(str(sec_uid)).set({"create_time": create_time, "video_id": video_id, "sec_uid": sec_uid, "username": username, "channel_id": str(channel.id)}, merge=True)
                        db_currency.document(str(interaction.user.id)).update({"balance": firestore.Increment(-5)})
                    except Exception as e:
                        embed = create_embed(description=f"{DATABASE_ICON}Failed to update database: {e}", colour=0xff2c2c)
                        await interaction.edit_original_response(embed=embed)
                        return
                    embed = create_embed(description=msg, colour=0x77dd77)
                    await interaction.edit_original_response(embed=embed)
                elif result and result.get('error'):
                    embed = create_embed(description=result['error'], colour=0xff2c2c)
                    await interaction.edit_original_response(embed=embed)
            except Exception as e:
                embed = create_embed(description=f"{ERROR_ICON} Failed to start monitoring TikTok user `{username}`. Error: {e}", colour=0xff2c2c)
                await interaction.edit_original_response(embed=embed)
#---------------------------------------------------------------------
        elif option.value == "list":
            db_tiktok = db_server.collection("tiktok")
            monitor_collection = db_tiktok.document(str(interaction.user.id)).collection("monitor").stream()
            usernames = []
            for doc in monitor_collection:
                data = doc.to_dict()
                if data and data.get("username"):
                    usernames.append(data["username"])
            if not usernames:
                embed = create_embed(description=f"{WARNING_ICON} You are not monitoring any TikTok users.", colour=0xffd700)
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return
            # Pagination logic (simple, since no package is in requirements.txt)
            page_size = 5
            pages = [usernames[i:i+page_size] for i in range(0, len(usernames), page_size)]
            embeds = []
            for idx, page in enumerate(pages):
                embed = discord.Embed(
                    title="Monitored TikTok Users",
                    description="\n".join(f"`{u}`\n" for u in page),
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Page {idx+1}/{len(pages)}")
                embeds.append(embed)
            # Send first page and add navigation if needed
            if len(embeds) == 1:
                await interaction.response.send_message(embed=embeds[0], ephemeral=False)
            else:
                class Paginator(discord.ui.View):
                    def __init__(self, embeds, author_id):
                        super().__init__(timeout=120)
                        self.embeds = embeds
                        self.index = 0
                        self.author_id = author_id
                        # Set initial button states
                        self.previous.disabled = True
                        if len(self.embeds) == 1:
                            self.next.disabled = True
                    async def interaction_check(self, interaction_button: discord.Interaction) -> bool:
                        if interaction_button.user.id != self.author_id:
                            await interaction_button.response.send_message("Only the command user can use these buttons.", ephemeral=True)
                            return False
                        return True
                    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji=discord.PartialEmoji(name="back", id=1372270406991609926))
                    async def previous(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                        if self.index > 0:
                            self.index -= 1
                            # Disable if now at first page
                            self.previous.disabled = self.index == 0
                            self.next.disabled = False
                            await interaction_button.response.edit_message(embed=self.embeds[self.index], view=self)
                    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji=discord.PartialEmoji(name="next", id=1372272834851635310))
                    async def next(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                        if self.index < len(self.embeds) - 1:
                            self.index += 1
                            # Disable if now at last page
                            self.next.disabled = self.index == len(self.embeds) - 1
                            self.previous.disabled = False
                            await interaction_button.response.edit_message(embed=self.embeds[self.index], view=self)
                await interaction.response.send_message(embed=embeds[0], view=Paginator(embeds, interaction.user.id), ephemeral=False)
            return
#---------------------------------------------------------------------
        elif option.value == "archive":
            try:
                if not username:
                    print("[archive] No username provided")
                    embed = create_embed(description=f"{WARNING_ICON} You must provide a TikTok username to archive.", colour=0xffd700)
                    await self.send_embed_safe(interaction, embed)
                    return
                if username.startswith("@"): 
                    username = username[1:]
                username = username.replace("@", "")
                # Send searching feedback to user
                embed = create_embed(description=f"{SEARCH_ICON} Searching for TikTok user `{username}`...", colour=0x6ac5fe)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                db_tiktok_archive = db_server.collection("tiktok_archive")
                archive_doc = None
                create_time = None
                try:
                    archive_stream = db_tiktok_archive.stream()
                    for doc in archive_stream:
                        data = doc.to_dict()
                        if data and data.get("username", "").lower() == username.lower():
                            create_time = data.get("create_time")
                            archive_doc = doc
                            break
                except Exception as e:
                    print(f"[archive] Database error: {e}")
                    embed = create_embed(description=f"{ERROR_ICON} Database error: {e}", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                guild = interaction.guild
                if not guild:
                    print("[archive] Guild not found")
                    embed = create_embed(description="Guild not found.", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                archive_channel = discord.utils.get(guild.channels, name="tik-archive")
                if not archive_channel or not isinstance(archive_channel, discord.ForumChannel):
                    print(f"[archive] 'tik-archive' forum channel not found")
                    embed = create_embed(description=f"{ERROR_ICON} 'tik-archive' forum channel not found.", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                thread = None
                if not archive_doc:
                    try:
                        # thread = await archive_channel.create_thread(
                        #     name=username,
                        #     content=f"Archive thread created for TikTok user `{username}` by {interaction.user.mention}.",
                        #     reason="TikTok archive request"
                        # )
                        # thread = thread.thread  # Add this line
                        six_months_ago = datetime.now(timezone.utc) - timedelta(days=30*6)
                        timestamp_6mo = int(six_months_ago.timestamp())
                        create_time = timestamp_6mo
                    except Exception as e:
                        print(f"[archive] Failed to create thread: {e}")
                        embed = create_embed(description=f"{ERROR_ICON} Failed to create thread: {e}", colour=0xff2c2c)
                        await self.send_embed_safe(interaction, embed)
                        return
                else:
                    try:
                        for t in archive_channel.threads:
                            if t.name.lower() == username.lower():
                                thread = t
                                break
                        if not thread:
                            print(f"[archive] Archive for {username} exists in database, but thread could not be found.")
                            embed = create_embed(description=f"{WARNING_ICON} Archive for `{username}` exists in database, but thread could not be found.", colour=0xffd700)
                            await self.send_embed_safe(interaction, embed)
                            return
                    except Exception as e:
                        print(f"[archive] Error finding thread: {e}")
                        embed = create_embed(description=f"{ERROR_ICON} Error finding thread: {e}", colour=0xff2c2c)
                        await self.send_embed_safe(interaction, embed)
                        return
                # --- TikTok API logic (fetch sec_uid, videos, etc.) ---
                try:
                    sec_uid = await self.fetch_tiktok_info(username)
                except Exception as e:
                    print(f"[archive] TikTok API error: {e}")
                    embed = create_embed(description=f"{ERROR_ICON} TikTok API error: {e}", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                if not sec_uid:
                    print(f"[archive] Could not find TikTok user {username}")
                    embed = create_embed(description=f"{ERROR_ICON} Could not find TikTok user `{username}`.", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                try:
                    sec_uid = str(sec_uid)
                    create_time = int(create_time)
                    
                    
                    videos = await fetch_video_info(sec_uid, 100, create_time)
                    print(videos)
                except Exception as e:
                    print(f"[archive] Failed to fetch TikTok videos: {e}")
                    embed = create_embed(description=f"{ERROR_ICON} Failed to fetch TikTok videos: {e}", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                if not videos:
                    print(f"[archive] No new videos found for {username} in the last 6 months.")
                    embed = create_embed(description=f"{WARNING_ICON} No new videos found for `{username}`", colour=0xffd700)
                    await self.send_embed_safe(interaction, embed)
                    return
                try:
                    if not archive_doc:
                        profile_pic = videos[0]['avatar']
                        async with aiohttp.ClientSession() as session:
                            async with session.get(profile_pic) as resp:
                                if resp.status == 200:
                                
                                    image_bytes = await resp.read()
                                    file = discord.File(io.BytesIO(image_bytes), filename="profile.jpg")
                                else:
                                    pass
                        
                        image_file = file
                        thread_with_message = await archive_channel.create_thread(
                            name=username,
                            content=f"Archive thread created for TikTok user `{username}` by {interaction.user.mention}.",
                            file=image_file,
                            reason="TikTok archive request"
                        )
                        thread = thread_with_message.thread 
                        print("naa dri 1")
                        # await self.send_image_url_as_file(thread, profile_pic, filename="profile.jpg", content="Profile picture:")
                    videos = sorted(videos, key=lambda x: x['create_time'])
                    new_create_time = videos[-1]['create_time']
                    new_video_id = videos[-1]['video_id']
                    print("naa dri 2")
                    
                    db_tiktok_archive.document(str(sec_uid)).set({"username": username, "sec_uid": sec_uid, "create_time": new_create_time, "video_id": new_video_id}, merge=True)
                    print("naa dri 3")
                    for video in videos:
                        try:
                            tiktok_url = f"https://www.tiktok.com/@{username}/video/{video['video_id']}"
                            file = await download_tiktok_video(video['video_id'], tiktok_url)
                            await thread.send(content=f"Archived by: {interaction.user.name}\n[[Watch on Tiktok]](<{tiktok_url}>)", file=file)
                        except Exception as e:
                            print(f"[archive] Failed to archive video {video['video_id']}: {e}")
                            await thread.send(content=f"{ERROR_ICON} Failed to archive video {video['video_id']}: {e}")
                except Exception as e:
                    print(f"[archive] Failed to archive videos: {e}")
                    embed = create_embed(description=f"{ERROR_ICON} Failed to archive videos: {e}", colour=0xff2c2c)
                    await self.send_embed_safe(interaction, embed)
                    return
                embed = create_embed(description=f"{IN_PROGRESS_ICON} Archive feature for `{username}` (sec_uid: `{sec_uid}`)\nFetched {len(videos) if videos else 0} videos from the last 6 months.\n\nArchive thread: [Go to topic]({thread.jump_url})", colour=0xffd700)
                await self.send_embed_safe(interaction, embed)
            except Exception as e:
                print(f"[archive] Unexpected error: {e}")
                embed = create_embed(description=f"{ERROR_ICON} Unexpected error: {e}", colour=0xff2c2c)
                await self.send_embed_safe(interaction, embed)
            return
#---------------------------------------------------------------------
        elif option.value == "scrape":
            embed = create_embed(description=f"{IN_PROGRESS_ICON} Service is still working in progress.", colour=0xff2c2c)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Invalid option.", ephemeral=True)
#---------------------------------------------------------------------
    async def start_monitoring(self, username):
        try:
            sec_uid = await self.fetch_tiktok_info(username)
            if not sec_uid:
                return {'error': f"{ERROR_ICON} Could not find TikTok user `{username}`."}
            video = await self.fetch_video_info(sec_uid, 1)
            if not video:
                return {'error': f"{ERROR_ICON} Could not fetch video info for `{username}`."}
            return {'success': True, 'sec_uid': sec_uid, 'video_id': video['video_id'], 'create_time': video['create_time']}
        except Exception as e:
            return {'error': f"{ERROR_ICON} Failed to start monitoring TikTok user `{username}`. Error: {e}"}

    async def fetch_tiktok_info(self, username):
        url = "https://tiktok-api23.p.rapidapi.com/api/user/info"
        headers = {
            "X-RapidAPI-Key": TIKTOK_API_KEY,
            "X-RapidAPI-Host": TIKTOK_API_HOST
        }
        params = {"uniqueId": username}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        try:
                            return data['userInfo']['user']['secUid']
                        except Exception:
                            return None
            except Exception as e:
                print(f"Error fetching tiktok.py: {e}")
                return None
        return None

    async def fetch_video_info(self, sec_uid, count):
        url = "https://tiktok-api23.p.rapidapi.com/api/user/posts"
        headers = {
            "X-RapidAPI-Key": TIKTOK_API_KEY,
            "X-RapidAPI-Host": TIKTOK_API_HOST
        }
        params = {"secUid": f"{sec_uid}", "count": f"{count}"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        try:
                            video_number = int
                            item_count = len(data['data']['itemList'])
                            if item_count == 1:
                                video_number = 0
                            elif item_count == 2:
                                video_number = 1
                            elif item_count == 3:
                                video_number = 2
                            elif item_count == 4:
                                video_number = 3
                        
                            create_time = data['data']['itemList'][video_number]['createTime']
                            video_id = data['data']['itemList'][video_number]['id']
                            return {
                            'create_time': create_time,
                            'video_id': video_id
                        }
                        except Exception:
                            return None
            except Exception as e:
                print(f"Error fetching tiktok.py: {e}")
                return None
        return None

    async def send_image_url_as_file(self, thread, image_url, filename="profile.jpg", content=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    file = discord.File(io.BytesIO(image_bytes), filename=filename)
                    await thread.send(content=content, file=file)
                else:
                    await thread.send(content="Failed to download image.")

    # On all subsequent responses, use followup if already responded
    def send_embed_safe(self, interaction, embed):
        try:
            if interaction.response.is_done():
                return interaction.followup.send(embed=embed, ephemeral=True)
            else:
                return interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[archive] send_embed_safe error: {e}")
            return interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TikTok(bot))
