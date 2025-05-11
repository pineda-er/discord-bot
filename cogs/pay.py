import discord
from discord import app_commands
from discord.ext import commands
import aiohttp  # <-- add this import
import asyncio  # <-- add this import
import os
import requests

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

class Pay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def admin_only():
        async def predicate(interaction: discord.Interaction):
            try:
                if not interaction.guild or not hasattr(interaction.user, "roles"):
                    await interaction.response.send_message(ADMIN_ONLY_TEXT, ephemeral=True)
                    return False
                admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
                if not admin_role or admin_role not in interaction.user.roles:
                    await interaction.response.send_message(ADMIN_ONLY_TEXT, ephemeral=True)
                    return False
                return True
            except Exception:
                try:
                    await interaction.response.send_message(ADMIN_ONLY_TEXT, ephemeral=True)
                except Exception:
                    pass
                return False
        return app_commands.check(predicate)

    @app_commands.command(name="pay", description="Display payment method information")
    @app_commands.describe(
        method="Payment method (e.g., gcash, paypal, crypto)",
        amount="Amount to pay (optional)",
        currency="Currency for crypto payments (usd/php, default: usd)"
    )
    @app_commands.choices(
        method=[
            app_commands.Choice(name="GCash", value="gcash"),
            app_commands.Choice(name="Maya", value="maya"),
            app_commands.Choice(name="GoTyme", value="gotyme"),
            app_commands.Choice(name="BDO", value="bank"),
            app_commands.Choice(name="Wise", value="wise"),
            app_commands.Choice(name="Paypal", value="paypal"),
            app_commands.Choice(name="BTC", value="btc"),
            app_commands.Choice(name="ETH", value="eth"),
            # Add more as needed
        ],
        currency=[
            app_commands.Choice(name="USD", value="usd"),
            app_commands.Choice(name="PHP", value="php"),
        ]
    )
    async def pay(
        self,
        interaction: discord.Interaction,
        method: app_commands.Choice[str],
        amount: int = None,
        currency: app_commands.Choice[str] = None
    ):
        try:
            # Define payment methods and their images
            payment_methods = {
                "gcash": {
                    "name": "GCash",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370506701328879799/IMG_1427.jpg?ex=681fbf54&is=681e6dd4&hm=bea72f4f4b749da781b9ade6065aaa463b22329a11d6d38875f19b78e82f70cb&=&format=webp&width=302&height=350"
                },
                "maya": {
                    "name": "Maya",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498401715617913/IMG_1428.jpg?ex=681fb799&is=681e6619&hm=dc606f02147348fa1b9677be2c0dd228b660b7c1ccc8dfc7bff1c46edda4ad00&=&format=webp&width=753&height=856"
                },
                "gotyme": {
                    "name": "GoTyme",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498401464221748/IMG_1429.jpg?ex=681fb799&is=681e6619&hm=9ad68b8462d8fe2df3198f8221005a2e666b0ce707273b2bd6b3ded09a75aab5&=&format=webp&width=706&height=855"
                },
                "bank": {
                    "name": "BDO",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498401225015508/IMG_1430.jpg?ex=681fb799&is=681e6619&hm=b0b4b8c07a98c5edca8fb619f4effba3e44847fc1a96bfea52cddc18a5648805&=&format=webp&width=579&height=856"
                },
                "wise": {
                    "name": "Wise",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498819325689977/wise.png?ex=681fb7fd&is=681e667d&hm=e96d6226f45c4db8ed390374e8662d1263e768a557743b046cd262ecda084ce2&=&format=webp&quality=lossless"
                },
                "paypal": {
                    "name": "Paypal",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1371087648525123625/qrcode_204136460_af1509989e62d3a4f363d06175f2e244.png?ex=6821dc60&is=68208ae0&hm=0cf67c7bebe47ecfbf7d14a90762942bf00fbceb0c4bc34d31c3292b0de8fb35&=&format=webp&quality=lossless&width=960&height=960"
                },
                "btc": {
                    "name": "BTC",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498400952389742/IMG_1431.jpg?ex=681fb799&is=681e6619&hm=833db302a6d5a1c06dcc1a11d4ae73c2ea3a2d7fb3c4de6250ca042a3680a517&=&format=webp&width=685&height=856"
                },
                "eth": {
                    "name": "ETH",
                    "image": "https://media.discordapp.net/attachments/1369637436610580523/1370498400583159858/IMG_1425.jpg?ex=681fb799&is=681e6619&hm=c995ae02b30ce93ae1594cda48f4139ad68a41b948462a4acc72ded645da67b7&=&format=webp&width=724&height=856"
                },
                # Add more methods as needed
            }

            method_key = method.value.lower()
            currency_value = "usd"
            if method_key in ["btc", "eth"]:
                if currency is not None:
                    currency_value = currency.value.lower()
                else:
                    currency_value = "usd"
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
            if method_key in ["btc", "eth"] and amount is not None:
                # Map method_key to CoinGecko IDs
                coingecko_ids = {"btc": "bitcoin", "eth": "ethereum"}
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
                                    crypto_amount_str = f"{crypto_amount:.8f}"  # Only the amount, no symbol
                                else:
                                    crypto_amount_str = f"{crypto_amount:.18f}"  # Only the amount, no symbol
                            else:
                                crypto_amount_str = "(Failed to fetch price)"
                                crypto_amount = None
                        else:
                            crypto_amount_str = "(Failed to fetch price)"
                            crypto_amount = None

            if method_key in payment_methods:
                info = payment_methods[method_key]
                description_parts = []
                if method_key == "gcash":
                    description_parts.append(GCASH_TEXT)
                elif method_key == "maya":
                    description_parts.append(MAYA_TEXT)
                elif method_key == "gotyme":
                    description_parts.append(GOTYME_TEXT)
                elif method_key == "paypal":
                    description_parts.append(PAYPAL_TEXT)
                if method_key == "btc":
                    description_parts.append(WALLET_ADDRESS_LABEL)
                    # Make BTC address copyable by using a code block
                    description_parts.append(f"`{BTC_ADDRESS.strip('`')}`")
                    description_parts.append("")  # Add space after address
                elif method_key == "eth":
                    description_parts.append(WALLET_ADDRESS_LABEL)
                    # Make ETH address copyable by using a code block
                    description_parts.append(f"`{ETH_ADDRESS.strip('`')}`")
                    description_parts.append("")  # Add space after address
                if amount is not None:
                    formatted_amount = f"{amount:,}"
                    if method_key in ["gcash", "maya", "gotyme", "bank"]:
                        description_parts.append(f"Amount: ₱{formatted_amount}")
                    elif method_key in ["btc", "eth","wise","paypal"]:
                        currency_label = "USD" if currency_value == "usd" else "PHP"
                        description_parts.append(f"Amount: {formatted_amount} {currency_label}")
                        if crypto_amount_str:
                            description_parts.append("")  # Add space before equivalent
                            if method_key == "btc":
                                description_parts.append(f"Equivalent: `{crypto_amount_str}` {BTC_ROLL_ICON}")
                            else:
                                description_parts.append(f"Equivalent: `{crypto_amount_str}` {ETC_ROLL_ICON}")
                    else:
                        description_parts.append(f"Amount: {formatted_amount}")
                description = "\n".join(description_parts) if description_parts else None
                embed = discord.Embed(
                    title=f"Payment Method: {info['name']}",
                    description=description,
                    color=discord.Color.blue()
                )
                embed.set_image(url=info["image"])

                # Add BTC/ETH sent button if needed
                if method_key in ["btc", "eth"]:
                    button_label = f"{method_key.upper()} Sent"
                    address = BTC_ADDRESS.strip("`") if method_key == "btc" else ETH_ADDRESS.strip("`")
                    
                    if crypto_amount:
                        print(f"crypto_amount_1: {crypto_amount}")
                        if method_key == "btc":
                            expected_amount = int(round(crypto_amount * 1e8))  # Satoshi
                            print(f"crypto_amount_2: {expected_amount}")
                        else:
                            expected_amount = int(round(crypto_amount * 1e18))  # Wei
                            print(f"crypto_amount_2: {expected_amount}")
                    else:
                        expected_amount = 0
                    # Use the calculated crypto_amount for transaction search
                    class ConfirmButton(discord.ui.View):
                        def __init__(self, address, expected_amount, method_key):  # MODIFIED parameter
                            super().__init__(timeout=None)
                            self.address = address
                            self.expected_amount = expected_amount  # MODIFIED: Use base units
                            self.method_key = method_key
                            self.sent_button = None  # Reference to the button
                            self.last_status_msg = None  # Track last status message
                            self.last_error_msg = None  # Track last error message

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
                                description="Currently searching for your transaction.\nThis may take a few minutes.",
                                color=discord.Color.orange()
                            )
                            status_message = await interaction_button.followup.send(embed=status_embed, ephemeral=False)
                            self.last_status_msg = status_message

                            found = False
                            tx_link = None
                            await asyncio.sleep(60)  # Wait 1 minute before first check

                            for i in range(3):  # Retry up to 3 times
                                if self.method_key == "btc":
                                    
                                    eth_results = search_btc_transaction(BTC_ADDRESS, self.expected_amount)
                                    
                                    for result in eth_results:
                                        if result["found"]:
                                            tx_link = result["tx_link"]
                                            found = True
                                            break
                                    
                                elif self.method_key == "eth":
                                    
                                    eth_results = search_eth_transaction(ETH_ADDRESS, self.expected_amount)
                                    
                                    for result in eth_results:
                                        if result["found"]:
                                            tx_link = result["tx_link"]
                                            found = True
                                            break

                                if found and tx_link:
                                    # Transaction found, update embed
                                    status_embed = discord.Embed(
                                        title=f"{SUCCESS_ICON} Transaction detected!",
                                        description=f"[View Transaction]({tx_link})",
                                        color=discord.Color.green()
                                    )
                                    await self.last_status_msg.edit(embed=status_embed, view=None)
                                    self.last_status_msg = None
                                    break
                                else:
                                    # Wait before retrying
                                    await asyncio.sleep(60)

                            if not found:
                                # No matching transaction found, re-enable button
                                if self.sent_button:
                                    self.sent_button.disabled = False
                                    try:
                                        parent_msg = await interaction_button.channel.fetch_message(interaction_button.message.id)
                                        await parent_msg.edit(view=self)
                                    except Exception:
                                        pass

                                # Delete the last status embed before sending error embed
                                if self.last_status_msg:
                                    try:
                                        await self.last_status_msg.delete()
                                    except Exception:
                                        pass
                                    self.last_status_msg = None

                                # Update embed with error message (send a new error embed and track it)
                                status_embed = discord.Embed(
                                    description=f"**{ERROR_ICON} No matching transaction found.**\n\nPlease contact support.",
                                    color=discord.Color.red()
                                )
                                error_msg = await interaction_button.followup.send(embed=status_embed, ephemeral=False)
                                self.last_error_msg = error_msg

                    await interaction.response.send_message(embed=embed, view=ConfirmButton(address, expected_amount, method_key))
                else:
                    await interaction.response.send_message(embed=embed)
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

    @admin_only()
    @app_commands.command(name="thanks", description="Thank a recent non-admin user for purchasing from the server")
    async def thanks(self, interaction: discord.Interaction):
        try:
            channel = interaction.channel
            guild = interaction.guild
            admin_role = discord.utils.get(guild.roles, name="Admin")
            messages = [message async for message in channel.history(limit=10)]
            thanked_user = None

            for message in messages:
                if message.author.bot:
                    continue
                member = guild.get_member(message.author.id)
                if member and (not admin_role or admin_role not in member.roles):
                    thanked_user = member
                    break

            if thanked_user:
                embed = discord.Embed(
                    title=THANK_YOU_TITLE,
                    description=THANKS_EMBED.format(mention=thanked_user.mention),
                    color=discord.Color.green()
                )
                customer_role = discord.utils.get(guild.roles, name="Customer")
                if customer_role and customer_role not in thanked_user.roles:
                    await thanked_user.add_roles(customer_role)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(NO_NONADMIN_FOUND, ephemeral=True)
        except Exception as e:
            try:
                await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Pay(bot))
