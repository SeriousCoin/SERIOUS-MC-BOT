import discord
import requests
import os

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
        url = f'https://api.dexscreener.io/latest/dex/pairs/cronos/{COIN_SYMBOL}'
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

client.run(DISCORD_TOKEN)