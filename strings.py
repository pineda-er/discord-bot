import os
from dotenv import load_dotenv
load_dotenv()

PAYMENT_METHOD_UNKNOWN = (
    "Unknown payment method: `{method}`. Please choose from: {choices}."
)

GCASH_TEXT = f"GCash Number: `{os.getenv('MOBILE_GLOBE')}`"
MAYA_TEXT = f"Maya Number: `{os.getenv('MOBILE_GOMO')}`"
GOTYME_TEXT = f"GoTyme Number: `{os.getenv('MOBILE_GOMO')}`"
PAYPAL_TEXT = "[Click Here](https://www.paypal.com/ncp/payment/93SMN2XTGGMHG)"
WALLET_ADDRESS_LABEL = "Wallet Address:"
BTC_ADDRESS = f"{os.getenv('BTC_ADDRESS')}"
ETH_ADDRESS = f"{os.getenv('ETH_ADDRESS')}"
LTC_ADDRESS = f"{os.getenv('LTC_ADDRESS')}"

TIKTOK_API_KEY = os.getenv("TIKTOK_API_KEY")
TIKTOK_API_HOST = os.getenv("TIKTOK_API_HOST")

THANKS_EMBED = (
    "Thank you {mention} for purchasing from the server!\n\n"
    "If you enjoyed your experience,\nplease consider sending a vouch message \nin"
    " <#1369992491692199999>!"
)

NO_NONADMIN_FOUND = "No recent non-admin user found to thank."

ETHERSCAN_API_KEY = f"{os.getenv('ETHERSCAN_API_KEY')}"
DIGITAL_ONE_GUILD_ID = f"{os.getenv('DIGITAL_ONE_GUILD_ID')}"
ADMIN_ROLE_ID = f"{os.getenv('ADMIN_ROLE_ID')}"

# -------------------------------------------------------------------
LOADING_ICON = "<a:loading:1370722180886691850>"
SUCCESS_ICON = "<a:success:1370826372041146432>"
ERROR_ICON = "<a:error:1370729292748685312>"
SEARCH_ICON = "<a:search:1372221113618268160>"
WARNING_ICON = "<a:warning:1372246429136851024>"
CONSOLE_ICON = "<a:console:1372222489379340288>"
DATABASE_ICON = "<a:database:1372222535646580866>"
IN_PROGRESS_ICON = "<a:coding:1372231548790771893>"
LIST_ICON = "<a:list:1372249855346606211>"

BTC_ROLL_ICON = "<a:btc_roll:1371012330636312677>"
ETC_ROLL_ICON = "<a:eth_roll:1371017688297639967>"
TIKTOK_CIRCLE_ICON = "<a:tiktok_circle:1372224465521479901>"

COINS_JUMP_ICON = "<a:coins_jump:1371031322335776849>"
# Admin only and error messages
ADMIN_ONLY_TEXT = "You must be an admin to use this command."
CRYPTO_AMOUNT_REQUIRED = "Amount is required for crypto payments (BTC/ETH/LTC). Please specify the amount."
SEARCHING_TRANSACTION_TEXT = "Currently searching for your transaction.\nThis may take a few minutes."
NO_MATCH_TEXT = f"**{ERROR_ICON} No matching transaction found.**\n\nPlease retry or contact support."
TRANSACTION_DETECTED_TITLE = "Transaction detected!"
THANK_YOU_TITLE = "Thank You!"
PAYMENT_METHOD_TITLE = "Payment Method: {name}"
EQUIVALENT_BTC_TEXT = "Equivalent: `{crypto_amount_str}`" +  f"{BTC_ROLL_ICON}"
EQUIVALENT_ETH_TEXT = "Equivalent: `{crypto_amount_str}`" + f"{ETC_ROLL_ICON}"
EQUIVALENT_LTC_TEXT = "Equivalent: `{crypto_amount_str}`"

ITEM_ALREADY_GRABBED = "Sorry! item was already grabbed"
LEVEL_TOO_LOW = "Sorry! Only members Level 5 and above can grab"
EX_CONVICT_CANNOT_GRAB = "Sorry! You are an Ex-Convict, you cannot grab items"
GENERIC_ERROR = "An error occurred: {error}"
DATABASE_ERROR = "Database error: {error}"

# Pagination and error messages
PAGINATION_OTHER_USER = "Can't change page from another member. Use **/coin shop**"
NO_ITEMS_IN_SHOP = "No items in shop..."
ITEM_NOT_FOUND = f"{ERROR_ICON} Item not found. Please check correct spelling of item"
NO_ITEM_FOUND = f"{ERROR_ICON} No item found, please check correct spelling of the item."
NO_ACCOUNT = f"{ERROR_ICON} You don't have an account.\n\nUse **/coin balance** before buying."
NOT_ENOUGH_BALANCE = f"{ERROR_ICON} You don't have enough balance for this item"
INVENTORY_EMPTY = "It's pretty empty around here..."
NO_ACCOUNT_FOUND = f"{ERROR_ICON} No account found.\n\n Use **/coin balance** or **/coin balance member [member_name]** first"
USED_ROLE_ITEM = f"{SUCCESS_ICON} " + "Used **{item_name}** and received {role_mention} role"
USED_RIO_ITEM = f"{SUCCESS_ICON} " + "Used **{item_name}**, Please check PM from Kafka"
USED_OTHER_ITEM = f"{SUCCESS_ICON} " + "Used **{item_name}**, although nothing happened..."
TRADED_ITEM = f"{SUCCESS_ICON} " + "Traded **{item_name}** to {mention}"
LEADERBOARD_EMPTY = "No leaderboard accounts yet"
CURRENCY_DEDUCTED = "{icon} **{amount:,}** was deducted from {mention}'s balance"
ITEM_REMOVED = "**{item_name}** removed from {mention}'s inventory"
CURRENCY_OR_ITEM_REQUIRED = f"{ERROR_ICON} currency or item should be given"
NOT_ENOUGH_TO_DROP = ":thumbsdown: Not enough Coins to drop"
NO_SUCH_ITEM_DROP = ":thumbsdown: No such item, please check item spelling"
SHOP_ADD_SUCCESS = f"{SUCCESS_ICON} " + "Successfully added `{item_name}` to shop items."
SHOP_REMOVE_SUCCESS = f"{SUCCESS_ICON} " + "Successfully removed **{item_name}** from shop items."
SHOP_REMOVE_FAIL = f"{ERROR_ICON} No item found, please check correct spelling of the item."
SHOP_PURCHASE_SUCCESS = f"{SUCCESS_ICON} " + "Successfully purchased **{item_name}**"
SHOP_GIVE_SUCCESS = f"{SUCCESS_ICON} " + "{mention} received {amount:,} Coins"
SHOP_TRANSFER_SUCCESS = f"{SUCCESS_ICON} " + "Transferred **{amount:,} Coins** to {mention}"
SHOP_TRANSFER_FAIL = f"{ERROR_ICON} Not enough balance to give/transfer"
SHOP_RECEIVER_FAIL = f"{ERROR_ICON} Receiver doesn't have an account.\n\nUse **/coin balance member[name]** before giving"
SHOP_SENDER_FAIL = f"{ERROR_ICON} You don't have an account.\n\nUse **/coin balance** before giving"
SHOP_MASSGIVE_SUCCESS = f"{SUCCESS_ICON} " + "**{total_members:,}** members with {role} role have been given **{amount:,}** Coins"
SHOP_MASSREMOVE_SUCCESS = f"{SUCCESS_ICON} " + "**{total_members:,}** members with {role} role have been deducted **{amount:,}** Coins"
SHOP_DROP_COIN = "Just dropped {icon} {amount:,} Coins!"
SHOP_DROP_ITEM = "Just dropped x1 - {item_name}"
SHOP_DROP_GRAB = "Grab it!"
SHOP_DROP_THUMBSUP = ":thumbsup:"
SHOP_DROP_HALANAHULOG = "**Hala nahulog!**"

SHOP_GRAB_COIN_SUCCESS = "**🎉 Congratulations {mention}, you got it! 🎉** \n \n **{currency:,} Coins** were added to your balance"
SHOP_GRAB_ITEM_SUCCESS = "**🎉 Congratulations {mention}, you got it! 🎉** \n \n **{item_name}** was added to your inventory"
MASS_GIVE_SUCCESS = f"{SUCCESS_ICON} " + "**{total_members:,}** members with {role} role have been given **{amount:,}** Coins"

ADD_SHOP_ITEM_SUCCESS = f"{SUCCESS_ICON} " + "Successfully added `{item_name}` to shop items."
REMOVE_SHOP_ITEM_SUCCESS = f"{SUCCESS_ICON} " + "Successfully removed **{item_name}** from shop items."
GIVE_RECEIVER_NO_ACCOUNT = f"{ERROR_ICON} Receiver doesn't have an account.\n\nUse **/coin balance member[name]** before giving"
GIVE_SENDER_NO_ACCOUNT = f"{ERROR_ICON} You don't have an account.\n\nUse **/coin balance** before giving"
GIVE_NOT_ENOUGH_BALANCE = f"{ERROR_ICON} Not enough balance to give/transfer"
GIVE_SUCCESS_ADMIN = f"{SUCCESS_ICON} " + "{mention} received {amount:,} Coins"
GIVE_SUCCESS = f"{SUCCESS_ICON} " + "Transferred **{amount:,} Coins** to {mention}"

