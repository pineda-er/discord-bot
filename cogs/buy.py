import discord
from discord import app_commands
from discord.ext import commands
import aiohttp  # <-- add this import
import asyncio  # <-- add this import
import os
import requests
from cogs.currency import give, create_embed

from strings import *

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
    Searches for a specific LTC transaction amount for a given wallet address using a free API.
    """
    if not wallet_address or amount is None:
        return []
    api_url = f"https://chain.so/api/v2/address/LTC/{wallet_address}"
    results = []
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        transactions = data.get("data", {}).get("txs", [])
        for tx in transactions:
            if tx.get("confirmed", False):
                # Fetch transaction details for outputs
                txid = tx.get("txid")
                tx_detail_url = f"https://chain.so/api/v2/tx/LTC/{txid}"
                try:
                    tx_detail_resp = requests.get(tx_detail_url, timeout=10)
                    tx_detail_resp.raise_for_status()
                    tx_detail = tx_detail_resp.json()
                    outputs = tx_detail.get("data", {}).get("outputs", [])
                    for output in outputs:
                        value = float(output.get("value", 0))
                        if value == amount:
                            results.append({
                                "tx_hash": txid,
                                "tx_link": f"https://chain.so/tx/LTC/{txid}",
                                "found": True
                            })
                except Exception:
                    continue
        return results
    except Exception as e:
        print(f"An error occurred while fetching LTC transaction data: {e}")
        return []

class Buy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy", description="Display payment method information")
    @app_commands.describe(
        method="Payment method (btc,eth)",
        amount="Amount to pay",
        # currency="Currency for crypto payments (usd/php, default: usd)"
    )
    @app_commands.choices(
        item=[
            app_commands.Choice(name="Coins", value="coins"),
        ],
        method=[
            app_commands.Choice(name="BTC", value="btc"),
            app_commands.Choice(name="ETH", value="eth"),
            app_commands.Choice(name="LTC", value="ltc"),  # Added LTC
            # Add more as needed
        ],
        amount=[
            app_commands.Choice(name="50 Coins ($5)", value="5"),
            app_commands.Choice(name="100 Coins ($10)", value="10"),
            app_commands.Choice(name="170 Coins ($15)", value="15"),
            app_commands.Choice(name="250 Coins ($20)", value="20"),
            app_commands.Choice(name="500 Coins ($45)", value="45"),
        ],
        # currency=[
        #     app_commands.Choice(name="USD", value="usd"),
        # ]
    )
    async def buy(
        self,
        interaction: discord.Interaction,
        item: app_commands.Choice[str],
        method: app_commands.Choice[str],
        amount: app_commands.Choice[str],
        # currency: None
    ):
        try:
            # Define payment methods and their images
            payment_methods = {
                "btc": {
                    "name": "BTC",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498400952389742/IMG_1431.jpg?ex=681fb799&is=681e6619&hm=833db302a6d5a1c06dcc1a11d4ae73c2ea3a2d7fb3c4de6250ca042a3680a517&=&format=webp&width=685&height=856"
                },
                "eth": {
                    "name": "ETH",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498400583159858/IMG_1425.jpg?ex=681fb799&is=681e6619&hm=c995ae02b30ce93ae1594cda48f4139ad68a41b948462a4acc72ded645da67b7&=&format=webp&width=724&height=856"
                },
                "ltc": {
                    "name": "LTC",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1371546324100579430/IMG_1458.jpg?ex=6823878d&is=6822360d&hm=853b01662083ef5f5d4337c593ec2f29b13e2aec206d13576c8b069ca77732e7&=&format=webp&width=768&height=960"  # Example LTC logo
                },
                # Add more methods as needed
            }

            method_key = method.value.lower()
            amount = int(amount.value)
            currency_value = "usd"
            # if method_key in ["btc", "eth"]:
            #     if currency is not None:
            #         currency_value = currency.value.lower()
            #     else:
            #         currency_value = "usd"
            # Require amount for BTC and ETH
            if method_key in ["btc", "eth"] and amount is None:
                await interaction.response.send_message(
                    CRYPTO_AMOUNT_REQUIRED,
                    ephemeral=True
                )
                return

            # --- Conversion logic for BTC/ETH ---
            crypto_amount = None
            crypto_amount_str = ""
            if method_key in ["btc", "eth", "ltc"] and amount is not None:
                # Map method_key to CoinGecko IDs
                coingecko_ids = {"btc": "bitcoin", "eth": "ethereum", "ltc": "litecoin"}
                cg_id = coingecko_ids[method_key]
                api_url = (
                    f"https://api.coingecko.com/api/v3/simple/price"
                    f"?ids={cg_id}&vs_currencies={currency_value}"
                )
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            price = data.get(cg_id, {}).get(currency_value)
                            if price:
                                crypto_amount = float(amount) / float(price)
                                if method_key == "btc":
                                    crypto_amount_str = f"{crypto_amount:.8f}"
                                elif method_key == "eth":
                                    crypto_amount_str = f"{crypto_amount:.18f}"
                                elif method_key == "ltc":
                                    crypto_amount_str = f"{crypto_amount:.8f}"
                            else:
                                crypto_amount_str = "(Failed to fetch price)"
                                crypto_amount = None
                        else:
                            crypto_amount_str = "(Failed to fetch price)"
                            crypto_amount = None

            if method_key in payment_methods:
                info = payment_methods[method_key]
                description_parts = []
                if method_key == "btc":
                    description_parts.append(WALLET_ADDRESS_LABEL)
                    description_parts.append(f"`{BTC_ADDRESS.strip('`')}`")
                    description_parts.append("")  # Add space after address
                elif method_key == "eth":
                    description_parts.append(WALLET_ADDRESS_LABEL)
                    description_parts.append(f"`{ETH_ADDRESS.strip('`')}`")
                    description_parts.append("")  # Add space after address
                elif method_key == "ltc":
                    description_parts.append(WALLET_ADDRESS_LABEL)
                    description_parts.append(f"`{LTC_ADDRESS.strip('`')}`")
                    description_parts.append("")  # Add space after address
                if amount is not None:
                    formatted_amount = f"{amount:,}"
                    if method_key in ["gcash", "maya", "gotyme", "bank"]:
                        description_parts.append(f"Amount: ₱{formatted_amount}")
                    elif method_key in ["btc", "eth", "ltc", "wise", "paypal"]:
                        currency_label = "USD" if currency_value == "usd" else "PHP"
                        description_parts.append(f"Amount: {formatted_amount} {currency_label}")
                        if crypto_amount_str:
                            description_parts.append("")  # Add space before equivalent
                            if method_key == "btc":
                                description_parts.append(f"Equivalent: `{crypto_amount_str}` {BTC_ROLL_ICON}")
                            elif method_key == "eth":
                                description_parts.append(f"Equivalent: `{crypto_amount_str}` {ETC_ROLL_ICON}")
                            elif method_key == "ltc":
                                description_parts.append(f"Equivalent: `{crypto_amount_str}` 🪙")
                    else:
                        description_parts.append(f"Amount: {formatted_amount}")
                description = "\n".join(description_parts) if description_parts else None
                embed = discord.Embed(
                    title=f"Payment Method: {info['name']}",
                    description=description,
                    color=discord.Color.blue()
                )
                embed.set_image(url=info["image"])

                # Add BTC/ETH/LTC sent button if needed
                if method_key in ["btc", "eth", "ltc"]:
                    button_label = f"{method_key.upper()} Sent"
                    if method_key == "btc":
                        address = BTC_ADDRESS.strip("`")
                    elif method_key == "eth":
                        address = ETH_ADDRESS.strip("`")
                    elif method_key == "ltc":
                        address = LTC_ADDRESS.strip("`")
                    else:
                        address = ""
                    if crypto_amount:
                        if method_key == "btc":
                            expected_amount = int(round(crypto_amount * 1e8))  # Satoshi
                        elif method_key == "eth":
                            expected_amount = int(round(crypto_amount * 1e18))  # Wei
                        elif method_key == "ltc":
                            expected_amount = int(round(crypto_amount * 1e8))  # Litoshi
                    else:
                        expected_amount = 0
                    # Use the calculated crypto_amount for transaction search
                    class ConfirmButton(discord.ui.View):
                        def __init__(self, address, expected_amount, method_key):
                            super().__init__(timeout=None)
                            self.address = address
                            self.usd_amount = amount
                            self.expected_amount = expected_amount
                            self.method_key = method_key
                            self.sent_button = None
                            self.last_status_msg = None
                            self.last_error_msg = None

                        @discord.ui.button(label=button_label, style=discord.ButtonStyle.success, custom_id=f"{method_key}_sent")
                        async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                            # Delete the previous status embed if it exists
                            if self.last_status_msg:
                                try:
                                    await self.last_status_msg.delete()
                                except Exception:
                                    pass
                                self.last_status_msg = None

                            # Also delete the previous error embed if it exists (for retries)
                            if hasattr(self, "last_error_msg") and self.last_error_msg:
                                try:
                                    await self.last_error_msg.delete()
                                except Exception:
                                    pass
                                self.last_error_msg = None

                            # Disable the button while searching
                            button.disabled = True
                            await interaction_button.response.edit_message(view=self)
                            self.sent_button = button

                            # Send initial status embed
                            status_embed = discord.Embed(
                                title=f"Checking {self.method_key.upper()} Transaction {LOADING_ICON}",
                                description=SEARCHING_TRANSACTION_TEXT,
                                color=discord.Color.orange()
                            )
                            status_message = await interaction_button.followup.send(embed=status_embed, ephemeral=True)
                            self.last_status_msg = status_message

                            found = False
                            tx_link = None
                            await asyncio.sleep(60)  # Wait 1 minute before first check

                            for i in range(3):  # Retry up to 3 times
                                if self.method_key == "btc":
                                    results = search_btc_transaction(BTC_ADDRESS, self.expected_amount / 1e8)
                                elif self.method_key == "eth":
                                    results = search_eth_transaction(ETH_ADDRESS, self.expected_amount / 1e18)
                                elif self.method_key == "ltc":
                                    results = search_ltc_transaction(LTC_ADDRESS, self.expected_amount / 1e8)
                                else:
                                    results = []
                                for result in results:
                                    if result["found"]:
                                        tx_link = result["tx_link"]
                                        found = True
                                        break
                                if found and tx_link:
                                    status_embed = discord.Embed(
                                        title=f"{SUCCESS_ICON} Transaction detected!",
                                        description=f"Sending coins to your balance\n[View Transaction]({tx_link})",
                                        color=discord.Color.green()
                                    )
                                    await self.last_status_msg.edit(embed=status_embed, view=None)
                                    self.last_status_msg = status_message
                                    if item.value == "coins":
                                        if self.usd_amount == 5:
                                            coin_amount = 50
                                        elif self.usd_amount == 10:
                                            coin_amount = 100
                                        elif self.usd_amount == 15:
                                            coin_amount = 170
                                        elif self.usd_amount == 20:
                                            coin_amount = 250
                                        elif self.usd_amount == 45:
                                            coin_amount = 500
                                        result = await give(self, interaction, interaction.user, coin_amount, bot=True)
                                        if result:
                                            await asyncio.sleep(10)
                                            embed = create_embed(description=result, colour=0x77dd77, footer="TIP: you can check shop items using /coin shop")
                                            await self.last_status_msg.edit(embed=embed, view=None)
                                            self.last_status_msg = None
                                    break
                                else:
                                    await asyncio.sleep(60)
                            if not found:
                                if self.sent_button:
                                    self.sent_button.disabled = False
                                    try:
                                        parent_msg = await interaction_button.channel.fetch_message(interaction_button.message.id)
                                        await parent_msg.edit(view=self)
                                    except Exception:
                                        pass
                                if self.last_status_msg:
                                    try:
                                        await self.last_status_msg.delete()
                                    except Exception:
                                        pass
                                    self.last_status_msg = None
                                status_embed = discord.Embed(
                                    description=NO_MATCH_TEXT,
                                    color=discord.Color.red()
                                )
                                error_msg = await interaction_button.followup.send(embed=status_embed, ephemeral=True)
                                self.last_error_msg = error_msg
                    await interaction.response.send_message(embed=embed, view=ConfirmButton(address, expected_amount, method_key), ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    PAYMENT_METHOD_UNKNOWN.format(
                        method=method.value,
                        choices=", ".join(payment_methods.keys())
                    ),
                    ephemeral=True
                )
        except Exception as e:
            try:
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Buy(bot))
