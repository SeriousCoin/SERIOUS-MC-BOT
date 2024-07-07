import discord
import requests
import asyncio
import os
import logging
from flask import Flask
from threading import Thread
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN_ID = 'serious-coin'
intents = discord.Intents.default()
client = discord.Client(intents=intents)

app = Flask(__name__)

def get_market_cap(token_id):
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        market_cap = data['market_data']['market_cap']['usd']
        logging.info(f"Market cap fetched: {market_cap}")
        return market_cap
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

async def update_bot_name():
    await client.wait_until_ready()
    while not client.is_closed():
        market_cap = get_market_cap(TOKEN_ID)
        if market_cap is not None:
            new_name = f"$SERIOUS MC: ${market_cap}"
            try:
                await client.user.edit(username=new_name)
                logging.info(f"Updated bot name to: {new_name}")
            except discord.errors.HTTPException as e:
                logging.error(f"Error updating bot name: {e}")
        else:
            logging.error("Failed to fetch market cap, skipping update.")
        await asyncio.sleep(300)  # Update every 5 minutes

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user.name}')

@app.route('/')
def home():
    return "Discord bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

async def main():
    # Start the Flask app in a separate thread to prevent blocking
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    async with client:
        client.loop.create_task(update_bot_name())
        await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
