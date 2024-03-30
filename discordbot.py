import json
from discord import Intents, Client
from responses import get_response
from sheets import DraftLeagueSheets


intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

config = None
with open('config.json') as json_file:
    config = json.load(json_file)

if config is None:
    raise NotImplementedError("Implement config generation")

TOKEN = config['discord-token']
   
draftBot = DraftLeagueSheets(config)


async def send_message(message, user_message: str) -> None:
    if not user_message:
        print('Message was empty because intents were not enabled probably')
        return
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]
        
    try:
        response = get_response(user_message, draftBot)
        if response:
            await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)
    
@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running")
    
@client.event
async def on_message(message) -> None:
    if message.author == client.user:
        return
    
    username = str(message.author)
    user_message = message.content
    chennel = str(message.channel)
    
    print(f'[{chennel}] {username}: "{user_message}"')
    await send_message(message, user_message)
    
def main() -> None:
    client.run(token=TOKEN)
    
if __name__ == '__main__':
    main()