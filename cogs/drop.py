import discord
from discord.ext import commands
from firebase_admin import firestore
from firebase_admin import storage
from google.cloud.firestore_v1.base_query import FieldFilter
import urllib.request

db = firestore.client()
bucket = storage.bucket()

dropper = None
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
        if(self.foo != True):
            
            embed = discord.Embed(
                description=f'**🎉 Congratulations {interaction.user.mention}, you got it! 🎉** \n \n DM {dropper} to claim',
                colour= 0x008000
            )
            await interaction.response.send_message(embed=embed)

            self.foo = True
            self.stop()
        else:
            await interaction.response.send_message("Sorry! this was already grabbed", ephemeral=True)
            self.stop
            
    
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
    @commands.has_any_role('Admin','Moderator','Sponsor')
    async def drop(self, ctx, *, item = None):
        """Sends an item that a member can grab/claim"""
        # if(item in ("50","100","nitro")):
        if(item):
            
            docs = db.collection("servers").document(str(ctx.message.guild.id)).collection("drop_items").where(filter=FieldFilter("name", "==", item)).stream()

            for doc in docs:
                # print(f"{doc.id} => {doc.to_dict()}")
                drop_item = doc.to_dict()
                
                # print(drop_item)
            
            #Connects to firebase firestore to get channel
            db_server = db.collection("servers").document(str(ctx.message.guild.id))
            db_channel = db_server.get().to_dict()
            db_channel = db_channel["drop_channel"]
            
            channel = self.bot.get_channel(int(db_channel))
            # file = discord.File(f'./image/{item}.jpg')
            # print(drop_item["image"])
            file = drop_item["image"]
            embed = discord.Embed(
                title=f"Someone dropped a {drop_item["name"]}!"
            )
            embed.set_image(url=file)
            embed.set_footer(text="Grab it!")
            view = SimpleView(timeout=10)
            
            message = await channel.send('**Hala nahulog!**', embed=embed, view=view)
            view.message = message
            
            global dropper 
            dropper = ctx.message.author.mention
            
            await ctx.message.add_reaction('✅')
            print(f"{ctx.message.author.name} dropped {drop_item["name"]}")
            await view.wait()
            await view.disable_all_items()
            
            
        
        elif(item is None):
            embed = discord.Embed(
                description='**❌ check available items using /drop check**',
                colour= 0xFF0000
            )
            await ctx.send(embed=embed)
            
    @drop.command(name='add', description='Add item to available drops')
    async def add(self, ctx, item_name: str, image: discord.Attachment):
        
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
        
    @drop.command(name='remove', description='Remove item from available drops')
    async def remove(self, ctx, item_name):

        # print(ctx.message.guild.id)
        db_server = db.collection("servers").document(str(ctx.message.guild.id))
        db_drop_items = db_server.collection("drop_items")
        db_remove_item = db_drop_items.where(filter=FieldFilter("name", "==", item_name)).stream()

        for doc in db_remove_item:
            # print(doc.id)
            db_drop_items.document(f'{doc.id}').delete()
        
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
            
        nameslist = '\n'.join(items)
            
        embed = discord.Embed(
            colour=0x6ac5fe
        )
        embed.add_field(name = 'Available drop items', value = nameslist)
        await ctx.send(embed=embed)
            
            
    @drop.error
    async def say_error(ctx, error):
        if isinstance(error, (commands.MissingRequiredArgument, commands.CommandError, commands.errors)):
                print(error)

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(Drop(bot))