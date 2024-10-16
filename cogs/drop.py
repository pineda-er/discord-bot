import discord
from discord.ext import commands
from firebase_admin import firestore
from firebase_admin import storage
from google.cloud.firestore_v1.base_query import FieldFilter
import urllib.request

db = firestore.client()
bucket = storage.bucket()

dropper = None

drop_restriction = "off"
drop_timeout = 60
class SimpleView(discord.ui.View):
    
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
        # print(interaction.user.roles)
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
                    embed = discord.Embed(
                        description=f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n DM {dropper} to claim',
                        colour= 0x008000
                )
                    await interaction.response.send_message(embed=embed)

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

# Define a cog class that inherits from commands.Cog
class Drop(commands.Cog):
    """commands: drop"""
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Drop ready")

    @commands.hybrid_group(name="drop", description="Sends an item that a member can grab/claim")
    @commands.has_any_role('AMS')
    async def drop(self, ctx, *, item : discord.Member | str):
        """Sends an item that a member can grab/claim"""
        # if(item in ("50","100","nitro")):
        # print(item)
        if(isinstance(item, str)):
            item = item.lower()
            
            docs = db.collection("servers").document(str(ctx.message.guild.id)).collection("drop_items").where(filter=FieldFilter("name", "==", item)).stream()

            for doc in docs:
                # print(f"{doc.id} => {doc.to_dict()}")
                drop_item = doc.to_dict()
                
                # print(drop_item)
            
            #Connects to firebase firestore to get channel
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_data = db_server.get().to_dict()
            db_channel = db_data["drop_channel"]
            db_drop_restriction = db_data["drop_restriction"]
            db_drop_timeout = db_data["drop_timeout"]
            
            drop_item_name = drop_item["name"]
            drop_item_name = str(drop_item_name)
            drop_item_name = drop_item_name.upper()
            channel = self.bot.get_channel(int(db_channel))
            # file = discord.File(f'./image/{item}.jpg')
            # print(drop_item["image"])
            file = drop_item["image"]
            embed = discord.Embed(
                title=f"Someone dropped a {drop_item_name}!"
            )
            embed.set_image(url=file)
            embed.set_footer(text="Grab it!")
            view = SimpleView(timeout=db_drop_timeout)
            
            message = await channel.send('**Hala nahulog!**', embed=embed, view=view)
            view.message = message
            
            global dropper 
            dropper = ctx.message.author.mention
            
            global drop_restriction
            drop_restriction = db_drop_restriction
            
            await ctx.message.add_reaction('✅')
            print(f"{ctx.message.author.name} dropped {drop_item["name"]}")
            await view.wait()
            await view.disable_all_items()
            
        elif(isinstance(item, discord.Member)):            
            #Connects to firebase firestore to get channel
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_data = db_server.get().to_dict()
            db_channel = db_data["drop_channel"]
            db_drop_restriction = db_data["drop_restriction"]
            db_drop_timeout = db_data["drop_timeout"]
            
            # drop_item_name = drop_item["name"]
            # drop_item_name = str(drop_item_name)
            # drop_item_name = drop_item_name.upper()
            channel = self.bot.get_channel(int(db_channel))
            
            embed = discord.Embed(
                title=f"Someone dropped {item.display_name} !"
            )
            embed.set_image(url=item.display_avatar)
            embed.set_footer(text="Grab them!")
            view = SimpleView(timeout=db_drop_timeout)
            
            message = await channel.send('**Hala nahulog!**', embed=embed, view=view)
            view.message = message
            
            # global dropper 
            dropper = ctx.message.author.mention
            
            # global drop_restriction
            drop_restriction = db_drop_restriction
            
            await ctx.message.add_reaction('✅')
            print(f"{ctx.message.author.name} dropped {item.display_name}")
            await view.wait()
            await view.disable_all_items()
            
        elif(item is None):
            embed = discord.Embed(
                description='**❌ check available items using /drop check**',
                colour= 0xFF0000
            )
            await ctx.send(embed=embed)
            
        
    @commands.has_any_role('AMS','Sponsor')
    @drop.command(name='add', description='Add item to available drops')
    async def add(self, ctx, item_name: str, image: discord.Attachment):
        item_name = item_name.lower()
        
        # print(image.content_type)
        
        embed = discord.Embed(
                description=f"** ✅ Successfully added `{item_name}` to drop items**",
                colour= 0x008000
            )
        await ctx.send(embed=embed)
        
        imgURL = image.url
        
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Chrome')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(imgURL, "./image/drop_item.png")
        
        fileName = f"{ctx.message.guild.id}/drop_item/{image.filename}"
        filePath = "./image/drop_item.png"
        blob = bucket.blob(fileName)
        blob.upload_from_filename(filePath)
        blob.upload_from_string
            
        blob.make_public()
            
        # print(blob.public_url)
        # print(image.url)
        # print(ctx.message.guild.id)
        db_server = db.collection("servers").document(str(ctx.message.guild.id))
        db_drop_items = db_server.collection("drop_items")
        db_drop_items.add({"name" : item_name, "image": blob.public_url})
        
        print(f"{item_name} has been added to drop list by {ctx.message.author.name}")
        
        # embed = discord.Embed(
        #         description=f"** ✅ Successfully added `{item_name}` to drop items**",
        #         colour= 0x008000
        #     )
        # await ctx.send(embed=embed)
    @commands.has_any_role('AMS','Sponsor')
    @drop.command(name='remove', description='Remove item from available drops')
    async def remove(self, ctx, item_name: str):
        item_name = item_name.lower()

        # print(ctx.message.guild.id)
        db_server = db.collection("servers").document(str(ctx.message.guild.id))
        db_drop_items = db_server.collection("drop_items")
        db_remove_item = db_drop_items.where(filter=FieldFilter("name", "==", item_name)).stream()

        for doc in db_remove_item:
            # print(doc.id)
            db_drop_items.document(f'{doc.id}').delete()
        # print(db_remove_item)
        
        embed = discord.Embed(
                description=f"** ✅ Successfully removed `{item_name}` from drop items**",
                colour= 0x008000
            )
        await ctx.send(embed=embed)
        print(f"{item_name} has been removed from drop list by {ctx.message.author.name}")
        
    @drop.command(name='check', description='Checks available drop items')
    async def check(self, ctx):
        items = []

        # print(ctx.message.guild.id)
        db_server = db.collection("servers").document(str(ctx.message.guild.id))
        db_drop_items = db_server.collection("drop_items")
        db_drop_items = db_drop_items.stream()
        
        for doc in db_drop_items:
            # print(doc.id)
            drop_item = doc.to_dict()
            # print(drop_item)
            items.append(drop_item["name"])
            # print(items)
            
        nameslist = '\n'.join(sorted(items))
            
        embed = discord.Embed(
            colour=0x6ac5fe
        )
        embed.add_field(name = 'Available drop items', value = nameslist)
        await ctx.send(embed=embed)
    
    @commands.has_any_role('AMS')
    @drop.command(name="restriction", description="ON/OFF member role restriction only who can grab/claim")
    async def restriction(self, ctx, status: str):
        status = status.lower()
        if(status in ("on","off")): 
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_server.set({"drop_restriction" : status}, merge=True)
            
            embed = discord.Embed(
                description=f"** ✅ Successfully set role restriction to {status.upper()}**",
                colour= 0x008000
            )
            await ctx.send(embed=embed)
            print(f"**Successfully set role restriction to {status.upper()}**")
            
        else:
             embed = discord.Embed(
                description=f"** ❌ Specify status ON or OFF **",
                colour= 0xFF0000
            )
             await ctx.send(embed=embed)
    @commands.has_any_role('AMS')
    @drop.command(name="timeout", description="set drop timeout on grab button. Default: 60 seconds")
    async def timeout(self, ctx, seconds: int):
        # status = status.lower()
        if(seconds): 
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_server.set({"drop_timeout" : seconds}, merge=True)
            
            embed = discord.Embed(
                description=f"** ✅ Successfully set timeout to {seconds} seconds**",
                colour= 0x008000
            )
            await ctx.send(embed=embed)
            print(f"Successfully set timeout to {seconds} seconds")
            
        else:
             embed = discord.Embed(
                description=f"** ❌ Specify timeout in seconds**",
                colour= 0xFF0000
            )
             await ctx.send(embed=embed)
             print(f"Successfully set timeout to {seconds} seconds")
            
            
        
        
    @drop.error
    async def say_error(ctx, error):
        if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
                print(error)

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Drop(bot))