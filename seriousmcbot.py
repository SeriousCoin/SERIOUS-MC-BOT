import discord
import requests
import os
from flask import Flask, jsonify

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

COIN_SYMBOL = 'SERIOUS'

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!marketcap'):
        # Fetch data from Dexscreener API
        url = f'https://api.dexscreener.io/latest/dex/pairs/cronos/0x18ab7692cc20F68A550b1Fdd749720CAd4a4894F'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if 'pair' in data:
                market_cap = data['pair']['market_cap']
                await message.channel.send(f'The market cap of {COIN_SYMBOL} is {market_cap}')
            else:
                await message.channel.send(f'Could not find market cap for {COIN_SYMBOL}')
        else:
            await message.channel.send(f'Error fetching data: {response.status_code}')

# Flask app for health check
app = Flask(__name__)

@app.route('/')
def index():
    return 'SERIOUS MC Bot is running!'

@app.route('/health')
def health_check():
    return jsonify({'status': 'UP'})

def run_discord_bot():
    client.run(DISCORD_TOKEN)

if __name__ == '__main__':
    import threading
    from concurrent.futures import ThreadPoolExecutor

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': int(os.environ.get('PORT', 5000))})
    flask_thread.start()

    # Start the Discord bot
    with ThreadPoolExecutor() as executor:
        executor.submit(run_discord_bot)