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
from typing import Callable, Optional
import string
import random
from strings import *

db = firestore.client()
bucket = storage.bucket()

voucher_code_global = None

# --- Utility Functions ---

def get_db_server(guild_id=None):
    if guild_id is None:
        guild_id = DIGITAL_ONE_GUILD_ID
    return db.collection("servers").document(str(guild_id))

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
                description=PAGINATION_OTHER_USER,
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
        try:
            for item in self.children:
                item.disabled = True
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception as e:
            print(f"Error disabling items: {e}")
    
    async def on_timeout(self) -> None:
        try:
            await self.disable_all_items()
        except Exception as e:
            print(f"Timeout error: {e}")
    
    @discord.ui.button(label="🫳 Grab", 
                       style=discord.ButtonStyle.success)
    async def response(self, interaction: discord.Interaction, button: discord.Button):
        try:
            print(self.item_name)
            if (drop_restriction == "on"):
                roles = ["5 — Pokemon",
                    "Server VIP","Sponsor"]
            else:
                roles = ["@everyone"]
            
            if not 'Ex-Convict' in str(interaction.user.roles):
                if any(role.name in roles for role in getattr(interaction.user, 'roles', [])):
                    if(getattr(self, 'foo', None) != True):
                        self.foo = True
                        db_server = get_db_server()
                        db_currency = db_server.collection("currency")
                        if self.currency:
                            text = SHOP_GRAB_COIN_SUCCESS.format(mention=interaction.user.mention, currency=self.currency)
                            embed = discord.Embed(
                            description=text,
                            colour= 0x008000
                            )
                            await interaction.response.send_message(embed=embed)
                            try:
                                db_currency_receiver = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
                                db_currency_sender = [d for d in db_currency.where(filter=FieldFilter("userID", "==", self.userID)).stream()]
                                db_currency_receiver_account = db_server.collection("currency").document(str(interaction.user.id))
                                db_currency_sender_account = db_server.collection("currency").document(str(self.userID))
                                if len(db_currency_receiver):
                                    for doc in db_currency_receiver:
                                        r_currency = doc.to_dict()
                                        db_currency_receiver_account.update({"balance": r_currency.get("balance", 0) + self.currency})
                                        for doc in db_currency_sender:
                                            s_currency = doc.to_dict()
                                            s_currency_remaining = s_currency.get("balance", 0) - self.currency
                                            db_currency_sender_account.update({"balance": s_currency_remaining})
                                else:
                                    db_currency_receiver_account.set({"mention": interaction.user.mention,"userID": interaction.user.id, "balance": self.currency}, merge=True)
                                    db_currency_sender_data = db_currency_sender_account.get().to_dict() or {"balance": 0}
                                    s_currency_remaining = db_currency_sender_data.get("balance", 0) - self.currency
                                    db_currency_sender_account.update({"balance": s_currency_remaining})
                            except Exception as e:
                                await interaction.followup.send(DATABASE_ERROR.format(error=e), ephemeral=True)
                        else:
                            text = SHOP_GRAB_ITEM_SUCCESS.format(mention=interaction.user.mention, item_name=string.capwords(self.item_name, sep=None))
                            embed = discord.Embed(
                            description=text,
                            colour= 0x008000
                            )
                            await interaction.response.send_message(embed=embed)
                            try:
                                db_currency_user = [d for d in db_currency.where(filter=FieldFilter("userID", "==", interaction.user.id)).stream()]
                                db_inventory_sender= db_currency.document(str(self.userID)).collection("inventory")
                                db_inventory_receiver = db_currency.document(str(interaction.user.id)).collection("inventory")
                                db_inventory_item = [d for d in db_inventory_sender.where(filter=FieldFilter("item_name", "==", self.item_name.lower())).limit(1).stream()]
                                db_inventory_item_receiver = [d for d in db_inventory_receiver.where(filter=FieldFilter("item_name", "==", self.item_name.lower())).limit(1).stream()]
                                if len(db_currency_user):
                                    for doc in db_inventory_item:
                                        inventory_item = doc.to_dict()
                                        item_name = inventory_item.get("item_name", "")
                                        item_name = string.capwords(item_name, sep = None)
                                        item_desc = inventory_item.get("desc", "")
                                        item_price = inventory_item.get("amount", 0)
                                        item_isRole = inventory_item.get("isRole", False)
                                        item_count = inventory_item.get("item_count", 1)
                                        if len(db_inventory_item_receiver):
                                            for doc in db_inventory_item_receiver:
                                                inventory_item_receiver = doc.to_dict()
                                                item_count_receiver = inventory_item_receiver.get("item_count", 1)
                                                db_inventory_item_receiver = db_inventory_receiver.document(str(doc.id))
                                                db_inventory_item_receiver.update({"item_count": item_count_receiver + 1})
                                        else:
                                            if item_isRole:
                                                item_role_id = inventory_item.get("roleID", None)
                                                item_role_mention = inventory_item.get("roleMention", None)
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
                                        item_name = inventory_item.get("item_name", "")
                                        item_name = string.capwords(item_name, sep = None)
                                        item_desc = inventory_item.get("desc", "")
                                        item_price = inventory_item.get("amount", 0)
                                        item_isRole = inventory_item.get("isRole", False)
                                        item_count = inventory_item.get("item_count", 1)
                                        if item_isRole:
                                            item_role_id = inventory_item.get("roleID", None)
                                            item_role_mention = inventory_item.get("roleMention", None)
                                            db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "roleID": item_role_id, "roleMention": item_role_mention, "item_count": 1})
                                        else:
                                            db_inventory_receiver.add({"item_name" : item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1})
                                        if item_count > 1:
                                            db_inventory_item = db_inventory_sender.document(str(doc.id))
                                            db_inventory_item.update({"item_count": item_count - 1})
                                        else: 
                                            db_inventory_sender.document(f'{doc.id}').delete()
                            except Exception as e:
                                await interaction.followup.send(DATABASE_ERROR.format(error=e), ephemeral=True)
                    else:
                        await interaction.response.send_message(ITEM_ALREADY_GRABBED, ephemeral=True)
                else: 
                    await interaction.response.send_message(LEVEL_TOO_LOW, ephemeral=True)
            else: 
                await interaction.response.send_message(EX_CONVICT_CANNOT_GRAB, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(GENERIC_ERROR.format(error=e), ephemeral=True)

class Currency(commands.Cog):
    """commands: currency"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Currency ready")
    
    group = app_commands.Group(name="coin", description="Coin Commands")
    
    @group.command(name="balance", description="Shows member Coin balance")
    async def balance(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        db_server = get_db_server()
        db_currency = get_db_currency(db_server)
        user = member or interaction.user
        user_currency = get_user_currency_doc(db_currency, user.id)
        name = f"{user.name}'s balance"
        avatar = user.avatar
        if user_currency:
            user_balance = user_currency[0].to_dict().get("balance", 0)
        else:
            db_currency.document(str(user.id)).set({"mention": user.mention, "userID": user.id, "balance": 0}, merge=True)
            user_balance = 0
        items = [f'{COINS_JUMP_ICON} **Coins: {user_balance:,}**']
        embed = create_embed(author=name, avatar=avatar, footer="TIP: Earn coins by joining events, giveaways and more!", colour=0x6ac5fe)
        embed.add_field(name=' ', value='\n \n '.join(items))
        await interaction.response.send_message(embed=embed)
    
    @group.command(name="transfer", description="Transfer Coins to another member")
    async def transfer(self, interaction: discord.Interaction,amount: int, member: discord.Member,):
       result = await give(self, interaction, member, amount, False) 
       if result:
          embed = create_embed(description=result, colour=0x77dd77, footer="TIP: you can check shop items using /coin shop")
          await interaction.response.send_message(embed=embed)
        
    @admin_only()
    @group.command(name="mass-give", description="Admin Only Command")
    async def mass_give(self, interaction: discord.Interaction, role: discord.Role, amount: int):
        items=[]
        db_server = get_db_server()
        db_data = db_server.get().to_dict()
        db_currency = get_db_currency(db_server)
        total_members = 0
        total_amount = 0
        await interaction.response.send_message(f"{LOADING_ICON}")
        for member in role.members:
            db_currency_receiver = [d for d in db_currency.where(filter=FieldFilter("userID", "==", member.id)).stream()]
            db_currency_receiver_account = db_server.collection("currency").document(str(member.id))
            total_members += 1
            total_amount += amount
            if len(db_currency_receiver):
                for doc in db_currency_receiver:
                    r_currency = doc.to_dict()
                    db_currency_receiver_account.update({"balance": r_currency["balance"] + amount})
            else:
                db_currency_receiver_account.set({"mention": member.mention,"userID": member.id, "balance": amount}, merge=True)
        db_server.set({"total_moonshards" : db_data["total_moonshards"] + total_amount}, merge=True)
        colour = 0x77dd77
        embed = discord.Embed(
            colour=colour,
            title = "",
            description=MASS_GIVE_SUCCESS.format(total_members=total_members, role=role.mention, amount=amount)
        )
        await interaction.delete_original_response()
        await interaction.followup.send(embed=embed)
                
    @admin_only()
    @group.command(name="add-shop-item", description="Admin Only Command")
    async def add_shop_item(self, interaction: discord.Interaction, item_name: str, description: str, amount: int, role: typing.Optional[discord.Role]):
        db_server = get_db_server()
        db_shop = db_server.collection("shop")
        if not role:
            db_shop.add({"item_name" : item_name.lower(), "desc": description.lower(), "amount": amount, "isRole": False})
        else:
            db_shop.add({"item_name" : item_name.lower(), "desc": description.lower(), "amount": amount, "isRole": True, "roleID": role.id, "roleMention": role.mention})
               
        await interaction.response.send_message(ADD_SHOP_ITEM_SUCCESS.format(item_name=item_name), ephemeral=True)
        
    @admin_only()
    @group.command(name="remove-shop-item", description="Admin Only Command")
    async def remove_shop_item(self, interaction: discord.Interaction, item_name: str):
        db_server = get_db_server()
        db_shop = db_server.collection("shop")
        db_shop_item = [d for d in db_shop.where(filter=FieldFilter("item_name", "==", item_name.lower())).stream()]
        if len(db_shop_item):
            for doc in db_shop_item:
                db_shop.document(f'{doc.id}').delete()
            await interaction.response.send_message(REMOVE_SHOP_ITEM_SUCCESS.format(item_name=item_name), ephemeral=True)
        else:
            await interaction.response.send_message(NO_ITEM_FOUND, ephemeral=True)
            
    @group.command(name="shop", description="Coin Shop")
    async def shop(self, interaction: discord.Interaction):
        db_server = get_db_server()
        shop_items = db_server.collection("shop")
        shop_docs = [d for d in shop_items.order_by("item_name").stream()]
        if not shop_docs:
            await send_error(interaction, NO_ITEMS_IN_SHOP, ephemeral=False)
            return
        items = []
        for doc in shop_docs:
            shop_item = doc.to_dict()
            item_name = string.capwords(shop_item["item_name"], sep=None)
            item_desc = shop_item["desc"]
            item_price = shop_item["amount"]
            item_isRole = shop_item["isRole"]
            if item_isRole:
                item_role_mention = shop_item["roleMention"]
                items.append({'text': f'**{item_name} [{item_role_mention}] — {COINS_JUMP_ICON} {item_price:,}**\n{item_desc}', 'price': item_price})
            else:
                items.append({'text': f'**{item_name} — {COINS_JUMP_ICON} {item_price:,}**\n{item_desc}', 'price': item_price})
        sorted_items = sorted(items, key=lambda element: element['price'], reverse=True)
        L = 5
        async def get_page(page: int):
            emb = create_embed(title="Coin Shop", colour=0x6ac5fe)
            offset = (page-1) * L
            emb.description = ""
            for user in sorted_items[offset:offset+L]:
                emb.description += f"{user['text']}\n \n"
            n = Pagination.compute_total_pages(len(sorted_items), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n
        await Pagination(interaction, get_page).navegate()
    
    @group.command(name="shop_buy", description="buy an item from Coin Shop")
    async def shop_buy(self, interaction: discord.Interaction, item_name: str):
        db_server = get_db_server()
        db_data = db_server.get().to_dict()
        db_currency = get_db_currency(db_server)
        db_shop = db_server.collection("shop")
        db_inventory = get_user_inventory(db_currency, interaction.user.id)
        db_inventory_item = get_inventory_item(db_inventory, item_name)
        db_shop_item = [d for d in db_shop.where(filter=FieldFilter("item_name", "==", item_name.lower())).stream()]
        db_currency_buyer = get_user_currency_doc(db_currency, interaction.user.id)
        if not db_shop_item:
            await send_error(interaction, ITEM_NOT_FOUND)
            return
        shop_item = db_shop_item[0].to_dict()
        item_price = shop_item["amount"]
        item_isRole = shop_item["isRole"]
        item_desc = shop_item["desc"]
        item_name = shop_item["item_name"]
        item_role_id = shop_item.get("roleID")
        item_role_mention = shop_item.get("roleMention")
        if not db_currency_buyer:
            await send_error(interaction, NO_ACCOUNT)
            return
        currency_buyer = db_currency_buyer[0].to_dict()
        balance = currency_buyer["balance"]
        buyer_balance = balance - item_price
        if buyer_balance < 0:
            await send_error(interaction, NOT_ENOUGH_BALANCE)
            return
        if db_inventory_item:
            doc = db_inventory_item[0]
            inventory_item = doc.to_dict()
            item_count = inventory_item["item_count"]
            db_inventory.document(str(doc.id)).update({"item_count": item_count + 1})
        else:
            add_data = {"item_name": item_name.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1}
            if item_isRole:
                add_data["roleID"] = item_role_id
                add_data["roleMention"] = item_role_mention
            db_inventory.add(add_data)
        db_currency.document(str(interaction.user.id)).update({"balance": buyer_balance})
        db_server.set({"total_moonshards": db_data["total_moonshards"] - item_price}, merge=True)
        item_name_cap = string.capwords(item_name, sep=None)
        text = SHOP_PURCHASE_SUCCESS.format(item_name=item_name_cap)
        embed = create_embed(description=text, colour=0x77dd77, footer="TIP: Use /coin inventory to check owned items")
        await interaction.response.send_message(embed=embed)
        
    @group.command(name="inventory", description="Check own or other members Inventory")
    async def inventory(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        db_server = get_db_server()
        db_currency = get_db_currency(db_server)
        user = member or interaction.user
        user_currency = get_user_currency_doc(db_currency, user.id)
        db_inventory = get_user_inventory(db_currency, user.id)
        inventory_docs = [d for d in db_inventory.order_by("item_name").stream()]
        name = f"{user.name}'s Inventory"
        avatar = user.avatar
        if not user_currency:
            await send_error(interaction, NO_ACCOUNT_FOUND)
            return
        if not inventory_docs:
            await send_error(interaction, INVENTORY_EMPTY, ephemeral=False)
            return
        items = []
        for doc in inventory_docs:
            inventory_item = doc.to_dict()
            item_name = string.capwords(inventory_item["item_name"], sep=None)
            item_desc = inventory_item["desc"]
            item_count = inventory_item["item_count"]
            item_isRole = inventory_item["isRole"]
            if item_isRole:
                item_role_mention = inventory_item["roleMention"]
                items.append(f'**[{item_count}x]  {item_name} [{item_role_mention}]**\n{item_desc}')
            else:
                items.append(f'**[{item_count}]  {item_name}**\n{item_desc}')
        L = 5
        async def get_page(page: int):
            emb = create_embed(title="", author=name, avatar=avatar, colour=0x6ac5fe)
            offset = (page-1) * L
            emb.description = ""
            for user in items[offset:offset+L]:
                emb.description += f"{user}\n \n"
            n = Pagination.compute_total_pages(len(items), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n
        await Pagination(interaction, get_page).navegate()
        
    @group.command(name="use-item", description="Use items in your inventory")
    async def use_item(self, interaction: discord.Interaction, item_name: str, override: typing.Optional[bool]):
        db_server = get_db_server()
        db_currency = get_db_currency(db_server)
        db_inventory = get_user_inventory(db_currency, interaction.user.id)
        db_inventory_item = get_inventory_item(db_inventory, item_name)
        if not db_inventory_item:
            await send_error(interaction, ITEM_NOT_FOUND)
            return
        doc = db_inventory_item[0]
        inventory_item = doc.to_dict()
        item_name_cap = string.capwords(inventory_item["item_name"], sep=None)
        item_count = inventory_item["item_count"]
        item_isRole = inventory_item["isRole"]
        if item_isRole:
            item_role_id = inventory_item["roleID"]
            item_role_mention = inventory_item["roleMention"]
            role = interaction.guild.get_role(item_role_id)
            await interaction.user.add_roles(role)
            text = USED_ROLE_ITEM.format(item_name=item_name_cap, role_mention=item_role_mention)
            colour = 0x77dd77
            ephemeral = False
        elif "rio" in item_name_cap.lower().split():
            voucher_code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
            voucher_code_global = "RIO-HA" + voucher_code
            member = interaction.user
            seller = interaction.guild.get_member(704356680472985651)
            embed_buyer = discord.Embed(
                colour=0x77dd77,
                title="Rio Island Voucher Activated!"
            )
            embed_buyer.add_field(name='PROMO CODE: ', value="RIO-HA" + voucher_code, inline=False)
            embed_buyer.set_image(url="https://firebasestorage.googleapis.com/v0/b/discordbot-1113e.appspot.com/o/Screenshot%202024-09-10%20004256.png?alt=media&token=bd966260-edce-425b-b80a-4d998cd8b12d")
            embed_buyer.add_field(name='USE IT IN: ', value="[Rio Oasis Island](https://discord.gg/rioasisland)", inline=False)
            embed_seller = discord.Embed(
                colour=0x77dd77,
                title="Voucher Activated!",
                timestamp=datetime.datetime.now()
            )
            embed_seller.add_field(name='VOUCHER: ', value=item_name_cap, inline=False)
            embed_seller.add_field(name='USERNAME: ', value=member.mention, inline=False)
            embed_seller.add_field(name='PROMO CODE: ', value="RIO-HA" + voucher_code, inline=False)
            embed_seller.set_footer(text='\u200b', icon_url=interaction.guild.icon.url)
            text = USED_RIO_ITEM.format(item_name=item_name_cap)
            colour = 0x77dd77
            ephemeral = False
            await interaction.response.send_message(embed=create_embed(description=text, colour=colour, footer="TIP: Use /coin trade-item to trade items with other members"), ephemeral=ephemeral)
            await member.send(embed=embed_buyer, view=ButtonView(voucher_code_global))
            await seller.send(embed=embed_seller)
            await ButtonView().wait()
            # No further response needed
            return
        else:
            text = USED_OTHER_ITEM.format(item_name=item_name_cap)
            colour = 0x77dd77
            ephemeral = False
        # Update or delete inventory
        if item_count > 1:
            db_inventory.document(str(doc.id)).update({"item_count": item_count - 1})
        else:
            db_inventory.document(f'{doc.id}').delete()
        await interaction.response.send_message(embed=create_embed(description=text, colour=colour, footer="TIP: Use /coin trade-item to trade items with other members"), ephemeral=ephemeral)
        
    @group.command(name="trade-item", description="Trade items with other members")
    async def trade_item(self, interaction: discord.Interaction, item_name: str, member: discord.Member):
        db_server = get_db_server()
        db_currency = get_db_currency(db_server)
        db_currency_user = get_user_currency_doc(db_currency, member.id)
        db_inventory_sender = get_user_inventory(db_currency, interaction.user.id)
        db_inventory_receiver = get_user_inventory(db_currency, member.id)
        db_inventory_item = get_inventory_item(db_inventory_sender, item_name)
        db_inventory_item_receiver = get_inventory_item(db_inventory_receiver, item_name)
        if not db_inventory_item:
            await send_error(interaction, ITEM_NOT_FOUND)
            return
        if not db_currency_user:
            await send_error(interaction, NO_ACCOUNT_FOUND + ".")
            return
        doc = db_inventory_item[0]
        inventory_item = doc.to_dict()
        item_name_cap = string.capwords(inventory_item["item_name"], sep=None)
        item_desc = inventory_item["desc"]
        item_price = inventory_item["amount"]
        item_isRole = inventory_item["isRole"]
        item_count = inventory_item["item_count"]
        # Add to receiver
        if db_inventory_item_receiver:
            receiver_doc = db_inventory_item_receiver[0]
            inventory_item_receiver = receiver_doc.to_dict()
            item_count_receiver = inventory_item_receiver["item_count"]
            db_inventory_receiver.document(str(receiver_doc.id)).update({"item_count": item_count_receiver + 1})
        else:
            add_data = {"item_name": item_name_cap.lower(), "desc": item_desc, "amount": item_price, "isRole": item_isRole, "item_count": 1}
            if item_isRole:
                add_data["roleID"] = inventory_item["roleID"]
                add_data["roleMention"] = inventory_item["roleMention"]
            db_inventory_receiver.add(add_data)
        # Remove from sender
        if item_count > 1:
            db_inventory_sender.document(str(doc.id)).update({"item_count": item_count - 1})
        else:
            db_inventory_sender.document(f'{doc.id}').delete()
        text = TRADED_ITEM.format(item_name=item_name_cap, mention=member.mention)
        embed = create_embed(description=text, colour=0x77dd77, footer="TIP: Use items by typing /coin use-item [item_name]")
        await interaction.response.send_message(embed=embed)
        
    @group.command(name="leaderboard", description="Coin Leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        db_server = get_db_server()
        db_currency = get_db_currency(db_server)
        leaderboard_docs = [d for d in db_currency.order_by("balance", direction=firestore.Query.DESCENDING).limit(10).stream()]
        if not leaderboard_docs:
            await send_error(interaction, LEADERBOARD_EMPTY, ephemeral=False)
            return
        items = []
        for rank, doc in enumerate(leaderboard_docs, 1):
            currency_leaderboard_item = doc.to_dict()
            member_mention = currency_leaderboard_item["mention"]
            member_balance = currency_leaderboard_item["balance"]
            items.append(f"**#{rank}**  {member_mention}\n Balance: **{member_balance:,}** {COINS_JUMP_ICON}")
        embed = create_embed(title=f"{COINS_JUMP_ICON} Coin Leaderboards", description='\n \n '.join(items), colour=0x6ac5fe, footer="TIP: Use items by typing /coin use-item [item_name]")
        await interaction.response.send_message(embed=embed)
    
    @admin_only()
    @group.command(name="remove", description="Admin Only Command")
    async def remove(self, interaction: discord.Interaction, member: discord.Member, currency: typing.Optional[int], item: typing.Optional[str]):
        db_server = get_db_server()
        db_data = db_server.get().to_dict()
        db_currency = get_db_currency(db_server)
        items = []
        colour = 0x77dd77
        if not currency and not item:
            await send_error(interaction, CURRENCY_OR_ITEM_REQUIRED)
            return
        if currency:
            user_currency_docs = get_user_currency_doc(db_currency, member.id)
            if user_currency_docs:
                for doc in user_currency_docs:
                    currency_user = doc.to_dict()
                    currency_user_balance = currency_user["balance"] - currency
                    db_currency_doc = db_currency.document(str(member.id))
                    db_currency_doc.update({"balance": max(currency_user_balance, 0)})
                items.append(CURRENCY_DEDUCTED.format(icon=COINS_JUMP_ICON, amount=currency, mention=member.mention))
                db_server.set({"total_moonshards": db_data["total_moonshards"] - currency}, merge=True)
            else:
                await send_error(interaction, NO_ACCOUNT_FOUND)
                return
        if item:
            db_inventory = get_user_inventory(db_currency, member.id)
            db_inventory_item = get_inventory_item(db_inventory, item)
            if db_inventory_item:
                for doc in db_inventory_item:
                    inventory_item = doc.to_dict()
                    inventory_item_name = inventory_item["item_name"]
                    db_inventory.document(f'{doc.id}').delete()
                items.append(ITEM_REMOVED.format(item_name=inventory_item_name, mention=member.mention))
            else:
                await send_error(interaction, ITEM_NOT_FOUND)
                return
        embed = create_embed(description='\n \n '.join(items), colour=colour, footer="TIP: you can check shop items using /coin shop")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @admin_only()
    @group.command(name="mass-remove", description="Admin Only Command")
    async def mass_remove(self, interaction: discord.Interaction, role: discord.Role, amount: int):
        db_server = get_db_server()
        db_data = db_server.get().to_dict()
        db_currency = get_db_currency(db_server)
        total_members = 0
        total_amount = 0
        await interaction.response.send_message(f"{LOADING_ICON}")
        for member in role.members:
            db_currency_receiver = get_user_currency_doc(db_currency, member.id)
            db_currency_receiver_account = db_currency.document(str(member.id))
            total_members += 1
            total_amount += amount
            if db_currency_receiver:
                for doc in db_currency_receiver:
                    r_currency = doc.to_dict()
                    r_currency_balance = r_currency["balance"] - amount
                    db_currency_receiver_account.update({"balance": max(r_currency_balance, 0)})
        db_server.set({"total_moonshards": db_data["total_moonshards"] - total_amount}, merge=True)
        embed = create_embed(
            colour=0x77dd77,
            description=SHOP_MASSREMOVE_SUCCESS.format(total_members=total_members, role=role.mention, amount=amount)
        )
        await interaction.delete_original_response()
        await interaction.followup.send(embed=embed)
    
    @admin_only()
    @group.command(name="drop", description="Drop coins or items")
    async def drop(self, interaction: discord.Interaction, currency: typing.Optional[int], item_name: typing.Optional[str]):
        db_server = get_db_server()
        db_data = db_server.get().to_dict()
        db_channel = db_data["drop_channel"]
        channel = interaction.guild.get_channel(int(db_channel))
        db_currency = get_db_currency(db_server)
        if not currency and not item_name:
            await send_error(interaction, CURRENCY_OR_ITEM_REQUIRED)
            return
        if currency:
            user_currency_docs = get_user_currency_doc(db_currency, interaction.user.id)
            if not user_currency_docs:
                await send_error(interaction, NOT_ENOUGH_TO_DROP)
                return
            currency_user = user_currency_docs[0].to_dict()
            currency_user_balance = currency_user["balance"]
            currency_user_remaining_balance = currency_user_balance - currency
            if currency_user_remaining_balance < 0:
                await send_error(interaction, NOT_ENOUGH_TO_DROP)
                return
            embed = create_embed(
                title=SHOP_DROP_COIN.format(icon=COINS_JUMP_ICON, amount=currency),
                colour=0x6ac5fe,
                author=interaction.user.name,
                avatar=interaction.user.avatar,
                footer=SHOP_DROP_GRAB
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1369637436610580523/1371029165171539968/wired-flat-298-coins-in-reveal.gif?ex=6821a5e9&is=68205469&hm=6fc75d7e6d51c6199104730949efb62b7885de0c47752a0675080fbf493befb6&")
            view = SimpleView(currency=currency, item_name=None, userID=interaction.user.id)
            message = await channel.send('', embed=embed, view=view)
            view.message = message
            await interaction.response.send_message(SHOP_DROP_THUMBSUP, ephemeral=True)
            await view.wait()
            await view.disable_all_items()
        if item_name:
            db_inventory = get_user_inventory(db_currency, interaction.user.id)
            db_inventory_item = get_inventory_item(db_inventory, item_name)
            if not db_inventory_item:
                await send_error(interaction, NO_SUCH_ITEM_DROP)
                return
            inventory_item = db_inventory_item[0].to_dict()
            inventory_item_name = inventory_item["item_name"]
            embed = create_embed(
                title=SHOP_DROP_ITEM.format(item_name=string.capwords(inventory_item_name, sep=None)),
                colour=0x6ac5fe,
                author=interaction.user.name,
                avatar=interaction.user.avatar,
                footer=SHOP_DROP_GRAB
            )
            embed.set_image(url="https://firebasestorage.googleapis.com/v0/b/discordbot-1113e.appspot.com/o/_652387f4-737d-4f53-b0d9-df487a9bba3c%20(1).jpg?alt=media&token=5ebc6085-4284-4efb-9b54-2209db1730a0")
            view = SimpleView(currency=None, item_name=inventory_item_name, userID=interaction.user.id)
            message = await channel.send(SHOP_DROP_HALANAHULOG, embed=embed, view=view)
            view.message = message
            await interaction.response.send_message(SHOP_DROP_THUMBSUP, ephemeral=True)
            await view.wait()
            await view.disable_all_items()
                    
# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Currency(bot))