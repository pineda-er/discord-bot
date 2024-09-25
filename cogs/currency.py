import typing
import discord
from discord.ext import commands
from discord import app_commands
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
from datetime import timedelta, datetime as datetimes
db = firestore.client()
from firebase_admin import storage
from typing import Callable, Optional, Union
import pytz
import string
import random

db = firestore.client()
bucket = storage.bucket()

voucher_code_global = None

class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Can't change page from another member. Use **/ms shop**",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navegate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        if self.index > self.total_pages // 2:
            self.children[2].emoji = "⏮️"
        else:
            self.children[2].emoji = "⏭️"
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.index <= self.total_pages//2:
            self.index = self.total_pages
        else:
            self.index = 1
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1

class ButtonView(discord.ui.View):
    def __init__(self, voucher_code_text: str):
        self.voucher_code = voucher_code_text
        super().__init__()
    
    @discord.ui.button(label="Print code as text", style=discord.ButtonStyle.green)
    async def function_name(self, int: discord.Interaction, button: discord.ui.Button):
        await int.response.send_message(self.voucher_code)
        
dropper = None

drop_restriction = "off"
drop_timeout = 60
class SimpleView(discord.ui.View):
    def __init__(self, currency, item_name, userID: int):
        self.currency = currency
        self.userID = userID
        self.item_name = item_name
        super().__init__(timeout=60)
    
    foo : bool = None
    
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        # await self.message.channel.send("Timedout")
        await self.disable_all_items()
    
    @discord.ui.button(label="🫳 Grab", 
                       style=discord.ButtonStyle.success)
    async def response(self, interaction: discord.Interaction, button: discord.ui.Button):
        # print(self.currency)
        # print(self.userID)
        print(self.item_name)
        if (drop_restriction == "on"):
            roles = ["5 — Pokemon",
                "Server VIP","Sponsor"]
        else:
            roles = ["@everyone"]
            
        # print(interaction.user.roles)
        if not 'Ex-Convict' in str(interaction.user.roles):
            if any(role.name in roles for role in interaction.user.roles):
                if(self.foo != True):
                    self.foo = True
                    # await interaction.response.send_message(f":partying_face:", ephemeral=True)
                    
                    db_server = db.collection("servers").document(str(interaction.guild_id))
                    db_currency = db_server.collection("currency")
                    
                    if self.currency:
                        text = f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n **{self.currency:,} Moon Shards** were added to your balance'
                        embed = discord.Embed(
                        description=text,
                        colour= 0x008000
                        )
                        await interaction.response.send_message(embed=embed)
                        
                        db_currency_receiver = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
                        db_currency_sender = [d for d in db_currency.where(filter=FieldFilter("userID", "==", self.userID)).stream()]
                        db_currency_receiver_account = db_server.collection("currency").document(str(interaction.user.id))
                        db_currency_sender_account = db_server.collection("currency").document(str(self.userID))
                    
                        if len(db_currency_receiver):
                            for doc in db_currency_receiver:
                                r_currency = doc.to_dict()
                                db_currency_receiver_account.update({"balance": r_currency["balance"] + self.currency})
                                for doc in db_currency_sender:
                                    s_currency = doc.to_dict()
                                    s_currency_remaining = s_currency["balance"] - self.currency
                                    db_currency_sender_account.update({"balance": s_currency_remaining})
                        else:
                            db_currency_receiver_account.set({"mention": interaction.user.mention,"userID": interaction.user.id, "balance": self.currency}, merge=True)
                            db_currency_sender_data = db_currency_sender_account.get().to_dict()
                            s_currency_remaining = db_currency_sender_data["balance"] - self.currency
                            db_currency_sender_account.update({"balance": s_currency_remaining})
                        # text = f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n {self.currency} Moon Shards were added to your balance'
                        
                    else:
                        text = f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n **{string.capwords(self.item_name, sep = None)}** was added to your inventory'
                        embed = discord.Embed(
                        description=text,
                        colour= 0x008000
                        )
                        await interaction.response.send_message(embed=embed)
                        
                        db_currency_user = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
                        db_inventory_sender= db_currency.document(str(self.userID)).collection("inventory")
                        db_inventory_receiver = db_currency.document(str(interaction.user.id)).collection("inventory")
                        db_inventory_item = [d for d in db_inventory_sender.where(filter=FieldFilter("item_name", "==", self.item_name.lower())).limit(1).stream()]
                        db_inventory_item_receiver = [d for d in db_inventory_receiver.where(filter=FieldFilter("item_name", "==", self.item_name.lower())).limit(1).stream()]
                        
                        if len(db_currency_user):
                            for doc in db_inventory_item:
                                inventory_item = doc.to_dict()
                                item_name = inventory_item["item_name"]
                                item_name = string.capwords(item_name, sep = None)
                                item_desc = inventory_item["desc"]
                                item_price = inventory_item["amount"]
                                item_isRole = inventory_item["isRole"]
                                item_count = inventory_item["item_count"]
                                
                                if len(db_inventory_item_receiver):
                                    for doc in db_inventory_item_receiver:
                                        inventory_item_receiver = doc.to_dict()
                                        item_count_receiver = inventory_item_receiver["item_count"]
                                        db_inventory_item_receiver = db_inventory_receiver.document(str(doc.id))
                                        db_inventory_item_receiver.update({"item_count": item_count_receiver + 1})
                                else:
                                    if item_isRole:
                                        item_role_id = inventory_item["roleID"]
                                        item_role_mention = inventory_item["roleMention"]
                                        db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "roleID": item_role_id, "roleMention": item_role_mention, "item_count": 1})
                                    else:
                                        db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1})
                                if item_count > 1:
                                    db_inventory_item = db_inventory_sender.document(str(doc.id))
                                    db_inventory_item.update({"item_count": item_count - 1})
                                else: 
                                    db_inventory_sender.document(f'{doc.id}').delete()
                        else:
                            db_currency_receiver_account = db_server.collection("currency").document(str(interaction.user.id))
                            db_currency_receiver_account.set({"mention": interaction.user.mention,"userID": interaction.user.id, "balance": 0}, merge=True)
                            db_inventory_receiver = db_currency.document(str(interaction.user.id)).collection("inventory")
                            
                            for doc in db_inventory_item:
                                inventory_item = doc.to_dict()
                                item_name = inventory_item["item_name"]
                                item_name = string.capwords(item_name, sep = None)
                                item_desc = inventory_item["desc"]
                                item_price = inventory_item["amount"]
                                item_isRole = inventory_item["isRole"]
                                item_count = inventory_item["item_count"]
                                
                                if item_isRole:
                                    item_role_id = inventory_item["roleID"]
                                    item_role_mention = inventory_item["roleMention"]
                                    db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "roleID": item_role_id, "roleMention": item_role_mention, "item_count": 1})
                                else:
                                    db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1})
                                if item_count > 1:
                                    db_inventory_item = db_inventory_sender.document(str(doc.id))
                                    db_inventory_item.update({"item_count": item_count - 1})
                                else: 
                                    db_inventory_sender.document(f'{doc.id}').delete()
            
                        # text = f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n {item_name} was added to your inventory'
                #     embed = discord.Embed(
                #         description=text,
                #         colour= 0x008000
                # )
                #     await interaction.response.send_message(embed=embed)

                    # self.stop()
                else:
                    await interaction.response.send_message("Sorry! item was already grabbed", ephemeral=True)
                    # self.stop()
            else: 
                await interaction.response.send_message("Sorry! Only members Level 5 and above can grab", ephemeral=True)
                
        else: await interaction.response.send_message("Sorry! You are an Ex-Convict, you cannot grab items", ephemeral=True)
                
    
    # @hello.error
    # async def say_error(self, interaction: discord.Interaction):
        # await interaction.response.send_message("Sorry!")
    #     self.stop()
    

class Currency(commands.Cog):
    """commands: currency"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Currency ready")
    
    group = app_commands.Group(name="ms", description="Moon Shards Commands")
    
    @group.command(name="balance", description="Shows member Moon Shard balance")
    async def balance(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        items=[]
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_currency = db_server.collection("currency")
        if not member:
            db_currency = db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()
            name = f"{interaction.user.name}'s balance"
            avatar = interaction.user.avatar
            
        else:
            db_currency = db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()
            name = f"{member.name}'s balance"
            avatar = member.avatar
        
        for doc in db_currency:
            # print(doc.id)
            currency = doc.to_dict()
            user_balance = (currency["balance"])
            items.append(f'<:moon_have:1285884278348976198> **Moon Shards: {user_balance:,}**')
        
        if not items:
            # db_server = db.collection("servers").document(str(interaction.guild.id))
            if not member:
                db_currency = db_server.collection("currency").document(str(interaction.user.id))
                db_currency.set({"mention": interaction.user.mention,"userID": interaction.user.id, "balance": int(0)}, merge=True)
                name = f"{interaction.user.name}'s balance"
                avatar = interaction.user.avatar
            else:
                db_currency = db_server.collection("currency").document(str(member.id))
                db_currency.set({"mention": member.mention,"userID": member.id, "balance": int(0)}, merge=True)
                name = f"{member.name}'s balance"
                avatar = member.avatar
            items.append("<:moon_have:1285884278348976198> **Moon Shards : 0**")
            
        nameslist = '\n \n '.join(sorted(items))
        
        embed = discord.Embed(
            colour = 0x6ac5fe,
            
        )
        embed.set_author(name = name, icon_url= avatar)
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: Earn moon shards by joining events, giveaways and more!")
        await interaction.response.send_message(embed=embed)
    
    @group.command(name="give", description="Give/Transfer Moon Shards to another member")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        items=[]
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_data = db_server.get().to_dict()
        db_currency = db_server.collection("currency")
        db_currency_receiver = [d for d in db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()]
        db_currency_sender = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
        if len(db_currency_receiver):
            if len(db_currency_sender):
                
                for doc in db_currency_receiver:
                    r_currency = doc.to_dict()
                    # print(member.id)
                    # print(r_currency["balance"])
                    # print(amount)
                    colour = 0x77dd77
                    isAdmin = discord.utils.get(interaction.guild.roles, name="Admin")
                    if isAdmin in interaction.user.roles:
                        db_currency = db_server.collection("currency").document(str(member.id))
                        db_currency.update({"balance": r_currency["balance"] + amount})
                        text = f'**✅ {member.mention} received {amount:,} Moon Shards**'
                        db_server.set({"total_moonshards" : db_data["total_moonshards"] + amount}, merge=True)
                    else:
                        for doc in db_currency_sender:
                            s_currency = doc.to_dict()
                            sender_balance = s_currency["balance"] - amount
                            if sender_balance >= 0:
                                db_currency_receiver = db_server.collection("currency").document(str(member.id))
                                db_currency_sender = db_server.collection("currency").document(str(interaction.user.id))
                                db_currency_receiver.update({"balance": r_currency["balance"] + amount})
                                db_currency_sender.update({"balance": s_currency["balance"] - amount})
                                text = f'✅ Transferred **{amount:,} Moon Shards** to {member.mention}'
                            else:
                                text = "⛔ Not enough balance to give/transfer"
                                colour = 0xff2c2c
                items.append(text)
            else:
                text = f"⛔ You don't have an account.\n\nUse **/ms balance** before giving"
                colour = 0xff2c2c
                items.append(text)      
        else:
            text = f"⛔ Receiver doesn't have an account.\n\nUse **/ms balance member[name]** before giving"
            colour = 0xff2c2c
            items.append(text)
        nameslist = '\n \n '.join(sorted(items))
        embed = discord.Embed(
            colour=colour,
        )
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: you can check shop items using /ms shop")
        await interaction.response.send_message(embed=embed)
        
    
    @app_commands.checks.has_any_role('Admin','AMS')
    @group.command(name="add-shop-item", description="AMS only command")
    async def add_shop_item(self, interaction: discord.Interaction, item_name: str, description: str, amount: int, role: typing.Optional[discord.Role]):
        # print(role)
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_shop = db_server.collection("shop")
        if not role:
            db_shop.add({"item_name" : item_name.lower(), "desc": description.lower(), "amount": amount, "isRole": False})
        else:
            db_shop.add({"item_name" : item_name.lower(), "desc": description.lower(), "amount": amount, "isRole": True, "roleID": role.id, "roleMention": role.mention})
        await interaction.response.send_message(f"**✅ Successfully added `{item_name}` to shop items.**", ephemeral=True)
        
    @app_commands.checks.has_any_role('Admin','AMS')
    @group.command(name="remove-shop-item", description="AMS only command")
    async def remove_shop_item(self, interaction: discord.Interaction, item_name: str):
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_shop = db_server.collection("shop")
        db_shop_item = [d for d in db_shop.where(filter=FieldFilter("item_name", "==", item_name.lower())).stream()]
        if len(db_shop_item):
            for doc in db_shop_item:
                db_shop.document(f'{doc.id}').delete()
            await interaction.response.send_message(f"✅ Successfully removed **{item_name}** from shop items.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⛔ No item found, please check correct spelling of the item.", ephemeral=True)
            
    @group.command(name="shop", description="Moon Shard Shop")
    async def shop(self, interaction: discord.Interaction):
        items = []
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        shop_items = db_server.collection("shop")
        shop_items = [d for d in shop_items.order_by("item_name").stream()]
        
        if len(shop_items):
            for doc in shop_items:
                # print(doc.id)
                shop_item = doc.to_dict()
                item_name = shop_item["item_name"]
                item_name = string.capwords(item_name, sep = None)
                item_desc = shop_item["desc"]
                item_price = shop_item["amount"]
                item_isRole = shop_item["isRole"]
                if item_isRole:
                    item_role_id = shop_item["roleID"]
                    item_role_mention = shop_item["roleMention"]
                items.append({'text': f'**{item_name} [{item_role_mention}] — <:moon_have:1285884278348976198> {item_price:,}**\n{item_desc}', 'price': item_price} if item_isRole else {'text': f'**{item_name} — <:moon_have:1285884278348976198> {item_price:,}**\n{item_desc}', 'price': item_price})

            # nameslist = '\n \n '.join(sorted(items))
            sorted_items = sorted(items, key=lambda element: element['price'], reverse=True)
            users = sorted_items
        else:
            items.append({'text': 'No items in shop...'})
            users = items
            
        
        # print(items)
        # print(nameslist)
        # print(users)
        # This is a long list of results
        # I'm going to use pagination to display the data
        L = 5    # elements per page
        async def get_page(page: int):
            emb = discord.Embed(title="Moon Shard Shop", description="", colour=0x6ac5fe)
            offset = (page-1) * L
            for user in users[offset:offset+L]:
                # print(list(user.values())[0])
                emb.description += f"{list(user.values())[0]}\n \n"
            # emb.set_author(name=f"Requested by {interaction.user}")
            n = Pagination.compute_total_pages(len(users), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n

        await Pagination(interaction, get_page).navegate()
    
    @group.command(name="buy-item", description="buy an item from Moon Shard Shop")
    async def buy_item(self, interaction: discord.Interaction, item_name: str):
        items=[]
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_data = db_server.get().to_dict()
        db_currency = db_server.collection("currency")
        db_shop = db_server.collection("shop")
        db_inventory = db_currency.document(str(interaction.user.id)).collection("inventory")
        db_inventory_item = [d for d in db_inventory.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]
        db_shop_item = [d for d in db_shop.where(filter=FieldFilter("item_name", "==", item_name.lower())).stream()]
        db_currency_buyer = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
        
        if len(db_shop_item):
            for doc in db_shop_item:
                # print(doc.id)
                shop_item = doc.to_dict()
                item_name = shop_item["item_name"]
                # item_name = string.capwords(item_name, sep = None)
                item_desc = shop_item["desc"]
                item_price = shop_item["amount"]
                item_isRole = shop_item["isRole"]
                if item_isRole:
                    item_role_id = shop_item["roleID"]
                    item_role_mention = shop_item["roleMention"]
                if len(db_currency_buyer):
                    for doc in db_currency_buyer:
                        # print(doc.id)
                        currency_buyer = doc.to_dict()
                        balance = currency_buyer["balance"]
                        mention = currency_buyer["mention"]
                        userID = currency_buyer["userID"]
                        buyer_balance = balance - item_price
                        if buyer_balance >= 0:
                            if len(db_inventory_item):
                                for doc in db_inventory_item:
                                    inventory_item = doc.to_dict()
                                    item_count = inventory_item["item_count"]
                                    db_inventory_item = db_inventory.document(str(doc.id))
                                    db_inventory_item.update({"item_count": item_count + 1})
                            else:
                                if item_isRole:
                                    db_inventory.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "roleID": item_role_id, "roleMention": item_role_mention, "item_count": 1})
                                else:
                                    db_inventory.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1})
                            db_currency_buyer = db_server.collection("currency").document(str(interaction.user.id))
                            db_currency_buyer.update({"balance": buyer_balance})
                            db_server.set({"total_moonshards" : db_data["total_moonshards"] - item_price}, merge=True)
                                # await interaction.response.send_message(f"**✅ Successfully removed `{item_name}` from shop items.**", ephemeral=True)
                            item_name = string.capwords(item_name, sep = None)
                            text = f"✅ Successfully purchased **{item_name}**"
                            colour = 0x77dd77
                            ephemeral = False
                            
                        else:
                            # await interaction.response.send_message(f"**not enough balance", ephemeral=True)
                            text = f"⛔ You don't have enough balance for this item"
                            colour = 0xff2c2c
                            ephemeral = True
                            
                else:
                    # await interaction.response.send_message(f"**no account found**", ephemeral=True)
                    text = f"⛔ You don't have an account.\n\nUse **/ms balance** before buying."
                    colour = 0xff2c2c
                    ephemeral = True
        else:
            # await interaction.response.send_message(f"**item not found**", ephemeral=True)
            text = f"⛔ Item not found. Please check correct spelling of item"
            colour = 0xff2c2c
            ephemeral = True
        
        items.append(text)
        nameslist = '\n \n '.join(sorted(items))
        embed = discord.Embed(
            colour=colour,
        )
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: Use /ms inventory to check owned items")
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        
    @group.command(name="inventory", description="Check own or other member Inventory")
    async def inventory(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        items = []
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_currency = db_server.collection("currency")
        # shop_items = [d for d in shop_items.stream()]
        
        if not member:
            db_currency_user = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
            db_inventory = [d for d in db_currency.document(str(interaction.user.id)).collection("inventory").order_by("item_name").stream()]
            name = f"{interaction.user.name}'s Inventory"
            avatar = interaction.user.avatar
            
        else:
            db_currency_user = [d for d in db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()]
            db_inventory = [d for d in db_currency.document(str(member.id)).collection("inventory").order_by("item_name").stream()]
            name = f"{member.name}'s Inventory"
            avatar = member.avatar
        
        if len(db_currency_user):
            # print("naay user")
            if len(db_inventory):
                # print("naay sulod")
                for doc in db_inventory:
                    inventory_item = doc.to_dict()  
                    # print(inventory_item)
                    item_name = inventory_item["item_name"]
                    item_name = string.capwords(item_name, sep = None)
                    item_desc = inventory_item["desc"]
                    item_price = inventory_item["amount"]
                    item_isRole = inventory_item["isRole"]
                    item_count = inventory_item["item_count"]
                    if item_isRole:
                        item_role_id = inventory_item["roleID"]
                        item_role_mention = inventory_item["roleMention"]
                    items.append(f'**[{item_count}]  {item_name} [{item_role_mention}]**\n{item_desc}' if item_isRole else f'**[{item_count}]  {item_name}**\n{item_desc}')
                    # print(items)
                # items = sorted(items)
                users = items
                
                L = 5    # elements per page
                async def get_page(page: int):
                    emb = discord.Embed(title="", description="", colour=0x6ac5fe)
                    emb.set_author(name = name, icon_url= avatar)
                    offset = (page-1) * L
                    for user in users[offset:offset+L]:
                        # print(user)
                        emb.description += f"{user}\n \n"
                    # emb.set_author(name=f"Requested by {interaction.user}")
                    n = Pagination.compute_total_pages(len(users), L)
                    emb.set_footer(text=f"Page {page} from {n}")
                    return emb, n
                
                await Pagination(interaction, get_page).navegate()
            else:
                # print("walay sulod")
                text = "It's pretty empty around here..."
                colour = 0xff2c2c
                error = True
                userExist = True
        else:
            # print("walay user")
            text = f"⛔ No account found.\n\n Use **/ms balance** or **/ms balance member [member_name]** first"
            colour = 0xff2c2c
            error = True
        
        if error:
            items.append(text)
            nameslist = '\n \n '.join(sorted(items))
            embed = discord.Embed(
                colour=colour,
            )
            if userExist:
                embed.set_author(name = name, icon_url= avatar)
            embed.add_field(name = ' ', value = nameslist)
            embed.set_footer(text="TIP: Use items by typing /ms use-item [item_name]")
            await interaction.response.send_message(embed=embed)
            
    @group.command(name="use-item", description="Use items in your inventory")
    async def use_item(self, interaction: discord.Interaction, item_name: str, override: typing.Optional[bool]):
        
        items = []
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_currency = db_server.collection("currency")
        db_inventory = db_currency.document(str(interaction.user.id)).collection("inventory")
        db_inventory_item = [d for d in db_inventory.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]
        
        if len(db_inventory_item):
            for doc in db_inventory_item:
                inventory_item = doc.to_dict()
                item_name = inventory_item["item_name"]
                item_name = string.capwords(item_name, sep = None)
                # item_desc = inventory_item["desc"]
                # item_price = inventory_item["amount"]
                item_count = inventory_item["item_count"]
                # print(item_count)
                item_isRole = inventory_item["isRole"]
                if item_isRole:
                    item_role_id = inventory_item["roleID"]
                    item_role_mention = inventory_item["roleMention"]
                    role = interaction.guild.get_role(item_role_id)
                    await interaction.user.add_roles(role)
                    # db_inventory.document(f'{doc.id}').delete()
                    # if item_count > 1:
                    #     db_inventory_item.update({"item_count": item_count - 1})
                    # else:
                    #     db_inventory.document(f'{doc.id}').delete()
                    text = f"✅ Used **{item_name}** and received {item_role_mention} role"
                    colour = 0x77dd77
                    ephemeral = False
                elif "rio" in item_name.lower().split():
                    # global voucher_code_global
                    voucher_code =''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
                    voucher_code_global = "RIO-HA" + voucher_code
                    member = interaction.user
                    seller = interaction.guild.get_member(704356680472985651)
                    
                    embed_buyer = discord.Embed(
                        colour = 0x77dd77,
                        title = "Rio Island Voucher Activated!"
                    )
                    embed_buyer.add_field(name = 'PROMO CODE: ', value = "RIO-HA" + voucher_code, inline=False)
                    embed_buyer.set_image(url="https://firebasestorage.googleapis.com/v0/b/discordbot-1113e.appspot.com/o/Screenshot%202024-09-10%20004256.png?alt=media&token=bd966260-edce-425b-b80a-4d998cd8b12d")
                    embed_buyer.add_field(name = 'USE IT IN: ', value = "[Rio Oasis Island](https://discord.gg/rioasisland)", inline=False)
                    
                    embed_seller = discord.Embed(
                        colour = 0x77dd77,
                        title = "Voucher Activated!",
                        timestamp= datetime.datetime.now()
                    )
                    embed_seller.add_field(name = 'VOUCHER: ', value = item_name, inline=False)
                    embed_seller.add_field(name = 'USERNAME: ', value = member.mention, inline=False)
                    embed_seller.add_field(name = 'PROMO CODE: ', value = "RIO-HA" + voucher_code, inline=False)
                    embed_seller.set_footer(text='\u200b',icon_url=interaction.guild.icon.url)
                    
                    text = f"✅ Used **{item_name}**, Please check PM from Kafka"
                    colour = 0x77dd77
                    ephemeral = False
                    
                    items.append(text)
                    nameslist = '\n \n '.join(sorted(items))
                    embed = discord.Embed(
                        colour=colour,
                    )
                    embed.add_field(name = ' ', value = nameslist)
                    embed.set_footer(text="TIP: Use /ms trade-item to trade items with other members")
                    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
                    
                    await member.send(embed=embed_buyer, view=ButtonView(voucher_code_global))
                    # await member.send(embed=embed_buyer)
                    await seller.send(embed=embed_seller)
                    await interaction.response.send_message(f"Please check PM from Kafka", ephemeral=True)
                    
                    await ButtonView().wait()
                else:
                    # if override:
                        text = f"✅ Used **{item_name}**, although nothing happened..."
                        colour = 0x77dd77
                        ephemeral = False
                    # else:
                    #     text = f"⛔ Non-role items can't be used for now. override option is available."
                    #     colour = 0xff2c2c
                    #     ephemeral = True
                if item_count > 1:
                    db_inventory_item = db_inventory.document(str(doc.id))
                    db_inventory_item.update({"item_count": item_count - 1})
                else:
                    db_inventory.document(f'{doc.id}').delete()
        else:
            text = f"⛔ Item not found. Please check correct spelling of item"
            colour = 0xff2c2c
            ephemeral = True
        
        items.append(text)
        nameslist = '\n \n '.join(sorted(items))
        embed = discord.Embed(
            colour=colour,
        )
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: Use /ms trade-item to trade items with other members")
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        
    @group.command(name="trade-item", description="Trade items with other members")
    async def trade_item(self, interaction: discord.Interaction, item_name: str, member: discord.Member):
        items = []
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_currency = db_server.collection("currency")
        db_currency_user = [d for d in db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()]
        db_inventory_sender= db_currency.document(str(interaction.user.id)).collection("inventory")
        db_inventory_receiver = db_currency.document(str(member.id)).collection("inventory")
        db_inventory_item = [d for d in db_inventory_sender.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]
        db_inventory_item_receiver = [d for d in db_inventory_receiver.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]
        
        if len(db_inventory_item):
            if len(db_currency_user):
                for doc in db_inventory_item:
                    inventory_item = doc.to_dict()
                    item_name = inventory_item["item_name"]
                    item_name = string.capwords(item_name, sep = None)
                    item_desc = inventory_item["desc"]
                    item_price = inventory_item["amount"]
                    item_isRole = inventory_item["isRole"]
                    item_count = inventory_item["item_count"]

                    if len(db_inventory_item_receiver):
                        for doc in db_inventory_item_receiver:
                            inventory_item_receiver = doc.to_dict()
                            item_count_receiver = inventory_item_receiver["item_count"]
                            db_inventory_item_receiver = db_inventory_receiver.document(str(doc.id))
                            db_inventory_item_receiver.update({"item_count": item_count_receiver + 1})
                    else:
                        if item_isRole:
                            item_role_id = inventory_item["roleID"]
                            item_role_mention = inventory_item["roleMention"]
                            db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "roleID": item_role_id, "roleMention": item_role_mention, "item_count": 1})
                        else:
                            db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1})
                    if item_count > 1:
                        db_inventory_item = db_inventory_sender.document(str(doc.id))
                        db_inventory_item.update({"item_count": item_count - 1})
                    else: 
                        db_inventory_sender.document(f'{doc.id}').delete()
                    text = f"✅ Traded **{item_name}** to {member.mention}"
                    colour = 0x77dd77
                    ephemeral = False
            else:
                text = f"⛔ No account found.\n\n Use **/ms balance** or **/ms balance member [member_name]** first."
                colour = 0xff2c2c
                error = True
        else:
            text = f"⛔ Item not found. Please check correct spelling of item"
            colour = 0xff2c2c
            ephemeral = True
            
        items.append(text)
        nameslist = '\n \n '.join(sorted(items))
        embed = discord.Embed(
            colour=colour,
        )
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: Use items by typing /ms use-item [item_name]")
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        
    @group.command(name="leaderboard", description="Moon Shard Leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        items = []
        
        db_server = db.collection("servers").document(str(interaction.guild_id))
        db_currency = db_server.collection("currency")
        db_currency_leaderboard  = [d for d in db_currency.order_by("balance", direction=firestore.Query.DESCENDING).limit(10).stream()]
        
        if len(db_currency_leaderboard):
            rank = 1
            for doc in db_currency_leaderboard:
                currency_leaderboard_item = doc.to_dict()
                member_mention = currency_leaderboard_item["mention"]
                member_balance = currency_leaderboard_item["balance"]
                items.append(f"**#{rank}**  {member_mention}\n Balance: <:moon_have:1285884278348976198> **{member_balance:,}**")
                rank = rank+1
        else:
            items.append(f"No leaderboard accounts yet")
            
        nameslist = '\n \n '.join(items)
        embed = discord.Embed(
                title = "<:moon_have:1285884278348976198> Moon Shard Leaderboards",
                colour = 0x6ac5fe,
            )
        
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: Use items by typing /ms use-item [item_name]")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.checks.has_any_role('Admin','AMS')
    @group.command(name="remove", description="AMS Only Command")
    async def remove(self, interaction: discord.Interaction, member: discord.Member, currency: typing.Optional[int], item: typing.Optional[str]):
        items  = []
        if not currency and not item:
            items.append(f"⛔ currency or item should be given")
            colour = 0xff2c2c
        else:
            colour = 0x77dd77
            db_server = db.collection("servers").document(str(interaction.guild_id))
            db_data = db_server.get().to_dict()
            db_currency = db_server.collection("currency")
            if currency:
                db_currency = [d for d in db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()]
            if item:
                db_inventory= db_currency.document(str(member.id)).collection("inventory")
                db_inventory_item = [d for d in db_inventory.where(filter=FieldFilter("item_name", "==", item.lower())).limit(1).stream()]
            if currency:
                if len(db_currency):
                    for doc in db_currency:
                        currency_user = doc.to_dict()
                        currency_user_balance = currency_user["balance"]
                        currency_user_balance = currency_user_balance - currency
                        db_currency = db_server.collection("currency").document(str(member.id))
                        if currency_user_balance >= 0:
                            db_currency.update({"balance": currency_user_balance})
                        else:
                            db_currency.update({"balance": 0})
                    items.append(f"<:moon_have:1285884278348976198> **{currency:,}** was deducted from {member.mention}'s balance")
                    db_server.set({"total_moonshards" : db_data["total_moonshards"] - currency}, merge=True)
                else:
                    items.append(f"⛔ No account found.\n\n Use **/ms balance** or **/ms balance member [member_name]** first")
                    colour = 0xff2c2c
                        
            if item:
                if len(db_inventory_item):
                    for doc in db_inventory_item:
                        inventory_item = doc.to_dict()
                        inventory_item_name = inventory_item["item_name"]
                        db_inventory.document(f'{doc.id}').delete()
                    items.append(f"**{inventory_item_name}** removed from {member.mention}'s inventory")
                else:
                    items.append(f"⛔ Item not found. Please check correct spelling of item")
                    colour = 0xff2c2c
                    
            
        nameslist = '\n \n '.join(sorted(items))
        embed = discord.Embed(
            colour=colour,
        )
        embed.add_field(name = ' ', value = nameslist)
        embed.set_footer(text="TIP: you can check shop items using /ms shop")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.checks.has_any_role('AMS', 'Sponsor')
    @group.command(name="drop", description="Drop moonshards or items")
    async def drop(self, interaction: discord.Interaction, currency: typing.Optional[int], item_name: typing.Optional[str]):
        items  = []  
        if not currency and not item_name:
            # text = "You should pick an option"
            # items.append(f"⛔ currency or item should be given")
            # colour = 0xff2c2c
            await interaction.response.send_message(f"⛔ currency or item should be given", ephemeral=True)
        else:
            colour = 0x77dd77
            db_server = db.collection("servers").document(str(interaction.guild_id))
            db_data = db_server.get().to_dict()
            db_channel = db_data["drop_channel"]
            db_drop_restriction = db_data["drop_restriction"]
            db_drop_timeout = db_data["drop_timeout"]
            channel = interaction.guild.get_channel(int(db_channel))
            db_currency = db_server.collection("currency")
            if currency:
                db_currency = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
                
                if len(db_currency):
                    for doc in db_currency:
                        currency_user = doc.to_dict()
                        currency_user_balance = currency_user["balance"]
                        currency_user_remaining_balance = currency_user_balance - currency
                        if currency_user_remaining_balance >= 0:
                            
                            embed = discord.Embed(
                                title=f"Just dropped <:moon_have:1285884278348976198> {currency:,} Moon Shards!"
                                )
                            # embed.set_image(url=item.display_avatar)
                            embed.set_footer(text="Grab it!")
                            embed.set_author(name = interaction.user.name, icon_url= interaction.user.avatar)
                            embed.set_image(url="https://firebasestorage.googleapis.com/v0/b/discordbot-1113e.appspot.com/o/_22245448-3bae-47f3-bca3-64a3689cfa7b-removebg-preview%20(2)%20(1).png?alt=media&token=0adc1ce9-44c7-46f7-8f45-f5bccff7c8a9")
                            view = SimpleView(currency = currency, item_name=None, userID = interaction.user.id)
            
                            message = await channel.send('**Hala nahulog!**', embed=embed, view=view)
                            view.message = message
            
                            # global dropper 
                            # dropper = ctx.message.author.mention
            
                            # global drop_restriction
                            # drop_restriction = db_drop_restriction
            
                            await interaction.response.send_message(f":thumbsup:", ephemeral=True)
                            # print(f"{ctx.message.author.name} dropped {item.display_name}")
                            await view.wait()
                            await view.disable_all_items()
                        else:
                            await interaction.response.send_message(f":thumbsdown: Not enough Moon Shards to drop", ephemeral=True)
            if item_name:
                db_inventory= db_currency.document(str(interaction.user.id)).collection("inventory")
                db_inventory_item = [d for d in db_inventory.where(filter=FieldFilter("item_name", "==", item_name.lower())).limit(1).stream()]
                
                if len(db_inventory_item):
                    for doc in db_inventory_item:
                        inventory_item = doc.to_dict()
                        inventory_item_name = inventory_item["item_name"]
                        
                        embed = discord.Embed(
                                title=f"Just dropped x1 - {string.capwords(inventory_item_name, sep = None)}"
                                )
                        # embed.set_image(url=item.display_avatar)
                        embed.set_footer(text="Grab it!")
                        embed.set_author(name = interaction.user.name, icon_url= interaction.user.avatar)
                        embed.set_image(url="https://firebasestorage.googleapis.com/v0/b/discordbot-1113e.appspot.com/o/_652387f4-737d-4f53-b0d9-df487a9bba3c%20(1).jpg?alt=media&token=5ebc6085-4284-4efb-9b54-2209db1730a0")
                        view = SimpleView(currency=None, item_name = inventory_item_name, userID = interaction.user.id)
            
                        message = await channel.send('**Hala nahulog!**', embed=embed, view=view)
                        view.message = message
            
                        # global dropper 
                        # dropper = ctx.message.author.mention
            
                        # global drop_restriction
                        # drop_restriction = db_drop_restriction
            
                        await interaction.response.send_message(f":thumbsup:", ephemeral=True)
                        # print(f"{ctx.message.author.name} dropped {item.display_name}")
                        await view.wait()
                        await view.disable_all_items()
                else:
                    await interaction.response.send_message(f":thumbsdown: No such item, please check item spelling", ephemeral=True)
            
        
        
    
            
                    
                    
                    
                
                
                
                
                
            
        
        
        
        
        
            
        
        
        
            
        
        
        
        
        
        
    
    
        
        
            
    
            

        
    
    
        
        
        

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Currency(bot))