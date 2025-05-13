import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import os

class TikTokMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tiktok_username = os.getenv('TIKTOK_USERNAME', 'kinomakalangittt')  # Set your TikTok username here or via env
        self.channel_id = int(os.getenv('TIKTOK_CHANNEL_ID', '1370027529678753903'))  # Set your channel ID here or via env
        self.last_video_id = None
        self.monitor_tiktok.start()

    def cog_unload(self):
        self.monitor_tiktok.cancel()

    @tasks.loop(minutes=5)
    async def monitor_tiktok(self):
        interval = self.monitor_tiktok.seconds // 60 if self.monitor_tiktok.seconds else 5
        print(f"[TikTokMonitor] Monitoring TikTok user: @{self.tiktok_username} every {interval} minutes...")
        await self.bot.wait_until_ready()
        if not self.channel_id:
            return
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        rapidapi_key = "8bc75d822bmsh82134bceaf3727dp1bf2c5jsn1eaa3f70b916"
        if not rapidapi_key:
            await channel.send('RAPIDAPI_KEY not set in environment.')
            return
        url = f'https://tiktok-info.p.rapidapi.com/user/posts?unique_id={self.tiktok_username}&count=1'
        headers = {
            'X-RapidAPI-Key': rapidapi_key,
            'X-RapidAPI-Host': 'tiktok-info.p.rapidapi.com'
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # The API returns a list of videos in data['itemList']
                        videos = data.get('itemList', [])
                        if videos:
                            video_id = videos[0].get('id')
                            if video_id and video_id != self.last_video_id:
                                self.last_video_id = video_id
                                await channel.send(f'New TikTok video posted by @{self.tiktok_username}: https://www.tiktok.com/@{self.tiktok_username}/video/{video_id}')
                    else:
                        await channel.send(f'Failed to fetch TikTok API for @{self.tiktok_username}. Status: {resp.status}')
            except Exception as e:
                await channel.send(f'Error fetching TikTok API data: {e}')

async def setup(bot):
    await bot.add_cog(TikTokMonitor(bot))
