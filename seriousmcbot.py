import discord
import requests
import asyncio
import os
import logging
import random
from flask import Flask, jsonify
from threading import Thread
from time import sleep
from hypercorn.asyncio import serve
from hypercorn.config import Config
from discord.ext import commands

# Configure logging
logging.basicConfig(level=logging.INFO)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN_ID = '0x18ab7692cc20F68A550b1Fdd749720CAd4a4894F'
GUILD_ID = int(os.getenv('GUILD_ID'))  # The ID of the server (guild) where you want to change the nickname

intents = discord.Intents.default()
intents.messages = True  # Enable message intent
intents.guilds = True  # Enable guilds intent
intents.message_content = True  # Ensure message content intent is enabled
bot = commands.Bot(command_prefix='!', intents=intents)

app = Flask(__name__)

GIF_URLS = [
    "https://tenor.com/view/wen-serious-crypto-meme-gif-16719925296958383434",
    "https://tenor.com/view/serious-crypto-meme-toast-great-gatsby-gif-5956985317763125460"
]

@app.route('/')
def home():
    return "Discord bot is running!"

@app.route('/heartbeat')
def heartbeat():
    return jsonify({"status": "alive"}), 200

def get_market_cap(token_id):
    url = f"https://api.dexscreener.com/latest/dex/pairs/cronos/{token_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        market_cap = data['pairs'][0]['fdv']  # Using FDV as market cap
        market_cap_k = int(market_cap // 1000)  # Round down to nearest thousand
        market_cap_k_str = f"{market_cap_k}K"
        logging.info(f"Market cap (FDV) fetched: {market_cap}, formatted: {market_cap_k_str}")
        return market_cap_k_str
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", 60))
            logging.error(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            sleep(retry_after)
            return get_market_cap(token_id)
        else:
            logging.error(f"Error fetching market cap: {e}")
            return None
    except KeyError as e:
        logging.error(f"Error parsing market cap data: {e}")
        return None

async def update_bot_nickname():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        logging.error(f"Guild with ID {GUILD_ID} not found")
        return
    
    while not bot.is_closed():
        market_cap = get_market_cap(TOKEN_ID)
        if market_cap is not None:
            new_nickname = f"MC: ${market_cap}"
            try:
                me = guild.me
                await me.edit(nick=new_nickname)
                logging.info(f"Updated bot nickname to: {new_nickname}")
            except discord.errors.HTTPException as e:
                logging.error(f"Error updating bot nickname: {e}")
        else:
            logging.error("Failed to fetch market cap, skipping update.")
        await asyncio.sleep(60)  # Update every minute

@bot.event
async def on_ready():
    logging.info(f'Logged in as {client.user.name}')

@bot.event
async def on_message(message):
    logging.info(f"Received message: {message.content}")
    logging.info(f"Message author: {message.author}, Bot user: {client.user}")
    if message.author == client.user:
        return

    if "!serious" in message.content.lower():
        gif_url = random.choice(GIF_URLS)
        await message.channel.send(gif_url)
        logging.info(f"Sent GIF: {gif_url}")

    if message.content.lower() == "!chart":
        await message.channel.send(
            "Click the button below to view the chart:",
            components=[
                discord.ui.Button(
                    style=discord.ButtonStyle.url,
                    label="Dexscreener",
                    url="https://dexscreener.com/cronos/0x18ab7692cc20f68a550b1fdd749720cad4a4894f"
                )
            ]
        )
        logging.info("Sent Dexscreener button")

async def run_flask():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    await serve(app, config)

async def main():
    flask_task = asyncio.create_task(run_flask())
    bot_task = asyncio.create_task(update_bot_nickname())
    
    await bot.start(DISCORD_TOKEN)
    await flask_task
    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
