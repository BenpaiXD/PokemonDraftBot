from random import choice, randint
from sheets import DraftLeagueSheets
from discord import Intents, Client
from constants import CONFIG_FILE_NAME, DEFAULT_LEAUGE, CONFIG_PARAMS
import json



def get_response(message, draftBot: DraftLeagueSheets) -> str:
    
    txt = message.content
    
    if txt == '':
        return "no message"
    
    
    channelId = str(message.channel.id)
    args = txt.split(" ")
    args = [arg for arg in args if arg != ""]
    
    args[0] = args[0].lower()
    
    if '!draft' == args[0]:
        if len(args) < 2:
            return "Please Specify the Pokémon you'd like to draft"
        elif len(args) > 2: 
            return f"Unexpected token {args[2]}, please try again"
        
        return draftBot.draft(args[1])
    
    if '!setdraftorder' == args[0]:
        order = draftBot.setRandomDraftOrder()
        msg = "Draft order is: \n"
        for user in order:
            msg += f"- {user}\n"
        return msg
    
    if '!setCoach' == args[0]:
        if len(args) != 4:
            return "Error: must be in format !setCoach <user> <role> <acr>"
        if len(args[3]) < 4:
            return "Acroynm must be 4 characters or less"
        
        with open(CONFIG_FILE_NAME) as json_file:
            config = json.load(json_file)
    
    #---------------------------------- all further commands are admin commands
    if not message.author.guild_permissions.administrator:
        return 'You do not have permission to use this command'
    
    
    if '!initleague' == args[0]:            
        if len(args) != 2:
            return "Error: command must be in format: !initLeague <leagueName>\n\nNote <leagueName> must be one word without parentheses"
        
        config = None
        with open(CONFIG_FILE_NAME, 'r') as json_file:
            config = json.load(json_file)
        
        print(config.keys())
        
        if str(channelId) in config['channelData']:
            return "Error: current channel already in use"
        
        if args[1] in config['leagues']:
            return f"Error: a league with the name {args[1]} already exists"
        
        config['channelData'][channelId] = {
            'leagueName': args[1],
            'admin': True,
            'name': message.channel.name
        }
        config['leagues'][args[1]] = DEFAULT_LEAUGE
        
        with open(CONFIG_FILE_NAME, 'w') as json_file:
            json.dump(config, json_file, indent=4)
            
        return f"Successfully created leauge {args[1]}"
    
    if '!setconfig' == args[0]:
        if len(args) != 3:
            return 'Error: command must be in format: !setConfig <parameter> <value>\n\nAvaliable parameters are: ' + str(CONFIG_PARAMS) 

        if args[1] not in CONFIG_PARAMS:
            return f'Error: invalid parameter "{args[1]}" \n\nAvaliable parameters are: ' + str(CONFIG_PARAMS) 

        if args[1] == 'sheet-id':
            if not draftBot.setSheet(args[2]):
                return "Failed to connect to sheet, please ensure the ID is correct and the account python-api@pokemondraftbot-418716.iam.gserviceaccount.com has read and write access"
            with open(CONFIG_FILE_NAME, 'r') as json_file:
                config = json.load(json_file)
            
            leagueName = config['channelData'][channelId]['leagueName']
            config['leagues'][leagueName]['sheet-id'] = args[2]
            
            with open(CONFIG_FILE_NAME, 'w') as json_file:
                json.dump(config, json_file, indent=4)

            return "Successfully set and connected to sheet"
        
        if args[1] == 'player-count':
            if not args[2].isnumeric():
                return "Failed to set player-count, value must be numeric"
            
            with open(CONFIG_FILE_NAME, 'r') as json_file:
                config = json.load(json_file)
            
            leagueName = config['channelData'][channelId]['leagueName']
            config['leagues'][leagueName]['player-count'] = int(args[2])
            
            with open(CONFIG_FILE_NAME, 'w') as json_file:
                json.dump(config, json_file, indent=4)

            return f"Successfully set player-count to {args[2]}"
