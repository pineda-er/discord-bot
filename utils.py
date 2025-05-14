import io
import json
import typing
import aiohttp
import discord
from discord import app_commands
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from strings import *
import requests

def get_db_server(guild_id=None):
    if guild_id is None:
        guild_id = DIGITAL_ONE_GUILD_ID
    return firestore.client().collection("servers").document(str(guild_id))

def get_db_currency(db_server):
    return db_server.collection("currency")

def get_user_currency_doc(db_currency, user_id):
    return [d for d in db_currency.where(filter=FieldFilter("userID", "==", user_id)).stream()]

def get_user_inventory(db_currency, user_id):
    return db_currency.document(str(user_id)).collection("inventory")

def get_inventory_item(db_inventory, item_name):
    return [d for d in db_inventory.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]

def create_embed(description=None, colour=0x6ac5fe, title=None, author=None, avatar=None, footer=None):
    embed = discord.Embed(description=description, colour=colour, title=title)
    if author and avatar:
        embed.set_author(name=author, icon_url=avatar)
    if footer:
        embed.set_footer(text=footer)
    return embed

def send_error(interaction, text, ephemeral=True):
    embed = create_embed(description=text, colour=0xff2c2c)
    return interaction.response.send_message(embed=embed, ephemeral=ephemeral)

def admin_only():
    return app_commands.checks.has_role(int(ADMIN_ROLE_ID))

async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int, bot: typing.Optional[bool]):
    db_server = get_db_server()
    db_data = db_server.get().to_dict()
    db_currency = get_db_currency(db_server)
    receiver_docs = get_user_currency_doc(db_currency, member.id)
    sender_docs = get_user_currency_doc(db_currency, interaction.user.id)
    if not receiver_docs:
        await send_error(interaction, GIVE_RECEIVER_NO_ACCOUNT)
        return
    if not sender_docs:
        await send_error(interaction, GIVE_SENDER_NO_ACCOUNT)
        return
    r_currency = receiver_docs[0].to_dict()
    s_currency = sender_docs[0].to_dict()
    if bot:
        isAdmin = True
    else:
        isAdmin = discord.utils.get(interaction.guild.get_role(ADMIN_ROLE_ID)) in interaction.user.roles
    if isAdmin:
        db_currency.document(str(member.id)).update({"balance": r_currency["balance"] + amount})
        db_server.set({"total_moonshards": db_data["total_moonshards"] + amount}, merge=True)
        text = GIVE_SUCCESS_ADMIN.format(mention=member.mention, amount=amount)
    else:
        sender_balance = s_currency["balance"] - amount
        if sender_balance < 0:
            await send_error(interaction, GIVE_NOT_ENOUGH_BALANCE)
            return
        db_currency.document(str(member.id)).update({"balance": r_currency["balance"] + amount})
        db_currency.document(str(interaction.user.id)).update({"balance": sender_balance})
        text = GIVE_SUCCESS.format(amount=amount, mention=member.mention)
    return text

def search_btc_transaction(wallet_address, amount):
    """
    Searches for a specific BTC transaction amount for a given wallet address using a free API.
    """
    if not wallet_address or amount is None:
        return []
    api_url = f"https://blockchain.info/rawaddr/{wallet_address}"
    results = []
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        transactions = data.get("txs", [])
        for tx in transactions:
            if tx.get("block_height", 0) > 0:
                for output in tx.get("out", []):
                    if output.get("value", 0) / 1e8 == amount:
                        results.append({
                            "tx_hash": tx.get("hash"),
                            "tx_link": f"https://www.blockchain.com/btc/tx/{tx.get('hash')}",
                            "found": True
                        })
        return results
    except Exception as e:
        print(f"An error occurred while fetching BTC transaction data: {e}")
        return []

def search_eth_transaction(wallet_address, amount):
    """
    Searches for a specific ETH transaction amount for a given wallet address using the provided API response format.
    """
    if not wallet_address or amount is None:
        return []
    api_url = f"https://api.blockchain.info/eth/account/{wallet_address}"
    results = []
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        transactions = data.get(wallet_address, {}).get("txns", [])
        for tx in transactions:
            if tx.get("blockNumber", 0) > 0:
                try:
                    value_eth = float(tx.get("value", 0)) / 1e18
                except Exception:
                    continue
                if value_eth == amount:
                    results.append({
                        "tx_hash": tx.get("hash"),
                        "tx_link": f"https://www.blockchain.com/eth/tx/{tx.get('hash')}",
                        "found": True
                    })
        return results
    except Exception as e:
        print(f"An error occurred while fetching ETH transaction data: {e}")
        return []

def search_ltc_transaction(wallet_address, amount):
    """
    Searches for a specific LTC transaction amount for a given wallet address using the BlockCypher API.
    """
    if not wallet_address or amount is None:
        return []
    api_url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{wallet_address}/full?limit=50"
    results = []
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        transactions = data.get("txs", [])
        for tx in transactions:
            if tx.get("confirmations", 0) > 0:
                for output in tx.get("outputs", []):
                    if wallet_address in output.get("addresses", []):
                        value = float(output.get("value", 0)) / 1e8
                        if value == amount:
                            results.append({
                                "tx_hash": tx.get("hash"),
                                "tx_link": f"https://live.blockcypher.com/ltc/tx/{tx.get('hash')}/",
                                "found": True
                            })
        return results
    except Exception as e:
        print(f"An error occurred while fetching LTC transaction data: {e}")
        return []

async def fetch_tiktok_info(self, username):
        url = "https://tiktok-api23.p.rapidapi.com/api/user/info"
        headers = {
            "X-RapidAPI-Key": "8bc75d822bmsh82134bceaf3727dp1bf2c5jsn1eaa3f70b916",
            "X-RapidAPI-Host": "tiktok-api23.p.rapidapi.com"
        }
        params = {"uniqueId": username}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                print(resp.status)
                if resp.status == 200:
                    data = await resp.json()
                    # Extract video info (customize as needed)
                    try:
                        sec_uid = data['userInfo']['user']['secUid']
                        print(f"SecUid: {sec_uid}")
                        return sec_uid
                    except Exception:
                        return None
        return None
    
async def fetch_video_info(sec_uid, count, create_time):
    url = "https://tiktok-api23.p.rapidapi.com/api/user/posts"
    headers = {
        "X-RapidAPI-Key": "8bc75d822bmsh82134bceaf3727dp1bf2c5jsn1eaa3f70b916",
        "X-RapidAPI-Host": "tiktok-api23.p.rapidapi.com"
    }
    params = {"secUid": f"{sec_uid}", "count": f"{count}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                try:
                    video_number = int
                    #count is 5
                    item_response = len(data['data']['itemList'])
                    count = int(count)
                    #item_count is 8
                    # print(f"count: {count}")
                    # print(f"item_count: {item_response}")
                    if item_response == count:
                        #if user has 0 pinned video
                            video_number = 0
                    elif item_response == count + 1:
                        #if user has 1 pinned video
                            video_number = 1
                    elif item_response == count + 2:
                        #if user has 2 pinned videos
                            video_number = 2
                    elif item_response == count + 3:
                        #if user has 3 pinned videos
                            video_number = 3
                    videos = []
                    old_create_time = create_time
                    for i in range(count):
                        if old_create_time >= data['data']['itemList'][video_number + i]['createTime']:
                            # print(f"{old_create_time} >= {data['data']['itemList'][video_number + i]['createTime']}")
                            continue
                        else:
                            create_time = data['data']['itemList'][video_number + i]['createTime']
                            video_id = data['data']['itemList'][video_number + i]['id']
                            videos.append({
                                'create_time': create_time,
                                'video_id': video_id
                            })
                    # print(videos)
                    return videos
                except Exception as e:
                    print(resp.status)
                    print("utils.py:" + e)
                    return None
    return None

async def get_tiktok_download_url(video_id: str, tiktok_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.tikwm.com/api/?url={tiktok_url}&hd=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                download_url = data.get('data', {}).get('play', None)
                return download_url
    return None

async def download_tiktok_video(video_id: str, tiktok_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.tikwm.com/api/?url={tiktok_url}&hd=1") as resp:
            if resp.status == 200:
                data = await resp.json()
                download_url = data.get('data', {}).get('play', None)
                print(f"Download URL: {download_url}")
                if download_url:
                    # Download the video file
                    async with session.get(download_url) as video_resp:
                        if video_resp.status == 200:
                            print(video_resp.status)
                            video_bytes = await video_resp.read()
                            file = discord.File(fp=io.BytesIO(video_bytes), filename=f"{video_id}.mp4")
                            # await channel.send(content=f"Latest video from `{username}`:\n[Link](<{tiktok_url}>)", file=file)
                            return file
