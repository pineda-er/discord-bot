# Import the required modules
import discord
import datetime
import os
from PIL import Image
from io import BytesIO
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from discord.ext import commands 
from dotenv import load_dotenv

# Create a Discord client instance and set the command prefix
intents = discord.Intents.all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

# Set the confirmation message when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):   
        if isinstance(error, commands.MissingRequiredArgument):
            print(error)
    
# on join server
@bot.event
async def on_member_join(user: discord.Member):
    my_image = Image.open("welcome.png")
    
    # edit user avatar into round
    av = user.avatar.replace(size=128)
    data = BytesIO(await av.read())
        
    pfp = Image.open(data)
    pfp = pfp.resize((200, 200))
        
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, outline='black', width=10, fill=255)
    mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    pfp.putalpha(mask)
        
    output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    output.save('output.png')
        
    # Get dimensions of each image
    width1, height1 = my_image.size
    width2, height2 = pfp.size
        
    # Find center pixel of outer image
    center_x, center_y = (width1/2), (height1/2)
        
    # Offset inner image to align its center
    im2_x = center_x - (width2/2)
    im2_y = center_y - (height2/2)
    print(im2_x,im2_y)
    # Paste inner image over outer image
    # back_im = im1.copy()
    # back_im.paste(im2,(im2_x, im2_y))
    
    welcome_font = ImageFont.truetype("ariblk.ttf", 50)
    name_font = ImageFont.truetype("ariblk.ttf", 30)
    welcome_color = (248,218,150) # RGB
    user_color = (48,255,41) # RGB
        
    draw = ImageDraw.Draw(my_image)
    draw.text((width1/2, 270),"WELCOME",welcome_color,font=welcome_font, anchor="mm", stroke_width=1, stroke_fill='#8e7339')
    draw.text((width1/2, 310),f'{user.name.upper()}',user_color,font=name_font, anchor="mm", stroke_width=1, stroke_fill='#0d7c09')
        
    my_image = my_image.copy()
    my_image.paste(pfp, (317, 40), pfp)
    my_image.save("profile.png")
        
    file = discord.File("profile.png")
    embed = discord.Embed(
    timestamp=datetime.datetime.now()
)
    embed.set_footer(text="HAve Fun! ♡")
    embed.set_image(url="attachment://profile.png")
    print(os.environ['WG_CHANNEL'])
    channel = bot.get_channel(int(os.environ['WG_CHANNEL']))
    await channel.send(f'Welcome to Honeymoon Avenue, {user.mention}', embed=embed, file=file)
    
    # channel = bot.get_channel(1239205900942835722)
    # file = discord.File("welcome.png")
    # embed = discord.Embed(
    #     # description= f'Welcome **{member.mention}** to the sever',
    #     # color=0xff55ff,
    #     timestamp=datetime.datetime.now()
    # )
    # embed.set_image(url="attachment://welcome.png")
    # await channel.send(f'Welcome to Honeymoon Avenue, {member.mention}', embed=embed, file=file)

# on leave server
@bot.event
async def on_member_remove(user: discord.Member):
    my_image = Image.open("goodbye.png")

    av = user.avatar.replace(size=128)
    data = BytesIO(await av.read())
        
    pfp = Image.open(data)
    pfp = pfp.resize((200, 200))
        
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    pfp.putalpha(mask)
        
    output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    output.save('output.png')
        
    # Get dimensions of each image
    width1, height1 = my_image.size
    width2, height2 = pfp.size
        
    # Find center pixel of outer image
    center_x, center_y = (width1/2), (height1/2)
        
    # Offset inner image to align its center
    im2_x = center_x - (width2/2)
    im2_y = center_y - (height2/2)
    print(im2_x,im2_y)
    # Paste inner image over outer image
    # back_im = im1.copy()
    # back_im.paste(im2,(im2_x, im2_y))
        
    goodbye_font = ImageFont.truetype("ariblk.ttf", 50)
    name_font = ImageFont.truetype("ariblk.ttf", 30)
    goodbye_color = (248,218,150) # RGB
    user_color = (140, 140, 140) # RGB
        
    draw = ImageDraw.Draw(my_image)
    draw.text((width1/2, 270),"GOODBYE",goodbye_color,font=goodbye_font, anchor="mm", stroke_width=1, stroke_fill='black')
    draw.text((width1/2, 310),f'{user.name.upper()}',user_color,font=name_font, anchor="mm", stroke_width=1, stroke_fill='gray')
        
    my_image = my_image.copy()
    my_image.paste(pfp, (317, 40), pfp,)
    my_image.save("profile.png")
        
    file = discord.File("profile.png")
    embed = discord.Embed(
    timestamp=datetime.datetime.now()
)
    embed.set_footer(text="Didn't HAve Fun! ;(")
    embed.set_image(url="attachment://profile.png")
    channel = bot.get_channel(int(os.environ['WG_CHANNEL']))
    await channel.send(f'Goodbye, {user.mention}', embed=embed, file=file)

# Set the commands for your bot
@bot.command()
async def greet(ctx):
    response = 'Hello, I am your discord bot'
    await ctx.send(response)
    

class SimpleView(discord.ui.View):
    
    foo : bool = None
    
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        # await self.message.channel.send("Timedout")
        await self.disable_all_items()
    
    @discord.ui.button(label="💸 Grab", 
                       style=discord.ButtonStyle.success)
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Congratulations {interaction.user.mention}, you got it!")
        self.foo = True
        self.stop()

@bot.command()
@commands.has_role("officers")
async def drop(ctx, amount = None):
    if(amount == "50" or amount == "100" or amount == "nitro"):
        channel = bot.get_channel(1239205900942835722)
        file = discord.File(f'{amount}.jpg')
        embed = discord.Embed(
        # description= f'Welcome **{member.mention}** to the sever',
        # color=0xff55ff,
        # timestamp=datetime.datetime.now()
    )
        embed.set_image(url=f"attachment://{amount}.jpg")
        embed.set_footer(text="Grab it before someone else does!")
        view = SimpleView(timeout=5)
        # button = discord.ui.Button(label="Click me")
        # view.add_item(button)
        
        await channel.send('**Hala nahulog!**', embed=embed, file=file)
        message = await channel.send(view=view)
        view.message = message
        
        
        await view.wait()
        await view.disable_all_items()
        
    elif(amount is None):
        await ctx.send('input `50` or `100`')
@drop.error
async def say_error(ctx, error):
    if isinstance(error, commands.CommandError):
            await ctx.send("Permission denied.")
        

# Retrieve token from the .env file
load_dotenv()
bot.run(os.getenv('TOKEN'))