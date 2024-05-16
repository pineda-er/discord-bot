import discord
import datetime
import os
from PIL import Image
from io import BytesIO
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from discord.ext import commands

class goodbye(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Event listener for when the bot is ready
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        my_image = Image.open("./image/goodbye.png")

        av = member.avatar.replace(size=128)
        data = BytesIO(await av.read())
            
        pfp = Image.open(data)
        pfp = pfp.resize((210, 210))
            
        bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask) 
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
        pfp.putalpha(mask)
            
        output = ImageOps.fit(pfp, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        output.save('./image/output.png')
            
        # Get dimensions of each image
        width1, height1 = my_image.size
        width2, height2 = pfp.size
            
        # Find center pixel of outer image
        center_x, center_y = (width1/2), (height1/2)
            
        # Offset inner image to align its center
        im2_x = center_x - (width2/2)
        im2_y = center_y - (height2/2)
        # print(im2_x,im2_y)
        # Paste inner image over outer image
        # back_im = im1.copy()
        # back_im.paste(im2,(im2_x, im2_y))
            
        goodbye_font = ImageFont.truetype("ariblk.ttf", 55)
        name_font = ImageFont.truetype("ariblk.ttf", 30)
        goodbye_color = (248,218,150) # RGB
        user_color = (140, 140, 140) # RGB
            
        draw = ImageDraw.Draw(my_image)
        draw.text((width1/2, 280),"GOODBYE",goodbye_color,font=goodbye_font, anchor="mm", stroke_width=1, stroke_fill='black')
        draw.text((width1/2, 320),f'{member.name.upper()}',user_color,font=name_font, anchor="mm", stroke_width=1, stroke_fill='gray')
            
        my_image = my_image.copy()
        my_image.paste(pfp, (317, 40), pfp,)
        my_image.save("./image/profile.png")
            
        file = discord.File("./image/profile.png")
        embed = discord.Embed(
        timestamp=datetime.datetime.now()
    )
        embed.set_footer(text="Didn't HAve Fun! ;(")
        embed.set_image(url="attachment://profile.png")
        channel = self.bot.get_channel(int(os.environ['GOODBYE_CHANNEL']))
        await channel.send(f'Goodbye, {member.mention}', embed=embed, file=file)

# Function to add this cog to the bot
    
async def setup(bot):
    await bot.add_cog(goodbye(bot))