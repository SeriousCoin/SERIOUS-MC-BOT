import discord
import requests
import asyncio
import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN_ID = 'serious-coin'
intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_market_cap(token_id):
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        market_cap = data['market_data']['market_cap']['usd']
        return market_cap
    except (requests.exceptions.HTTPError, KeyError) as e:
        print(f"Error fetching market cap: {e}")
        return None

async def update_bot_name():
    await client.wait_until_ready()
    while not client.is_closed():
        market_cap = get_market_cap(TOKEN_ID)
        if market_cap is not None:
            new_name = f"SERIOUS MC: ${market_cap}"
            try:
                await client.user.edit(username=new_name)
                print(f"Updated bot name to: {new_name}")
            except discord.errors.HTTPException as e:
                print(f"Error updating bot name: {e}")
        else:
            print("Failed to fetch market cap, skipping update.")
        await asyncio.sleep(300)  # Update every 5 minutes

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

async def main():
    async with client:
        client.loop.create_task(update_bot_name())
        await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
