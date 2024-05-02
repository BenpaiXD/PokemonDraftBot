from random import choice, randint
from sheets import DraftLeagueSheets
from discord import Intents, Client
from constants import CONFIG_FILE_NAME, DEFAULT_LEAUGE_CONFIG, CONFIG_PARAMS
import json




def get_response(message, draftBot: DraftLeagueSheets) -> str:
    
    txt = message.content
    
    if txt == '':
        return 
    
    config = None
    try: 
        with open(CONFIG_FILE_NAME) as json_file:
            config = json.load(json_file)
    except:
        return "Failed to load config, please contact developer"
    
    if config is None: 
        return "Failed to load config, please contact developer"
    
    
    channelId = str(message.channel.id)
    
    args = txt.split(" ")
    args = [arg for arg in args if arg != ""]
    args[0] = args[0].lower()
    
    leagueName = config['channelData'][channelId]['leagueName'] if args[0] != '!initleague' else None
    if leagueName is not None:
        draftBot.setConfig(config, leagueName)

    if channelId not in config['channelData'] and args[0] != '!initleague':
        return None
    
    if '!draft' == args[0]:
        if config['channelData'][channelId]['type'] not in {'draft', 'transactions'}:
            return 'Error: channel not for drafting'
            
        if leagueName not in config['userData'][str(message.author.id)]['leagues']:
            return "Error: you are not authorized to draft for this league"
        
        if not config['leagues'][leagueName]['draft-enabled']:
            return 'Draft is not currently enabled'
        
        if len(args) < 2:
            return "Please Specify the Pokémon you'd like to draft"
        if len(args) > 2: 
            return f"Unexpected token {args[2]}, please try again"
        
        if config['channelData'][channelId]['type'] == 'draft':
            coachName = message.author.name
            
            if coachName != config['leagues'][leagueName]['draft-turn']:
                return "Error: it is not your turn to draft, next up is " + config['leagues'][leagueName]['draft-turn']
                
            draftOrder = draftBot.getDraftOrder()
            
            
            draftOrderIndex = draftOrder.index(coachName)
            
            response = draftBot.draft(args[1], coachName, draftOrderIndex)
            
            if not response[0]:
                return response[1]
            
            if config['leagues'][leagueName]['draft-direction'] == 'down':
                if draftOrderIndex + 1 == config['leagues'][leagueName]["player-count"]:
                    config['leagues'][leagueName]["draft-direction"] = 'up'
                else:
                    config['leagues'][leagueName]["draft-turn"] = draftOrder[draftOrderIndex + 1]
            else:
                if draftOrderIndex - 1 < 0:
                    config['leagues'][leagueName]["draft-direction"] = 'down'
                else:
                    config['leagues'][leagueName]["draft-turn"] = draftOrder[draftOrderIndex - 1]
            
            saveConfig(CONFIG_FILE_NAME, config)
            
            user_id = getIDByName(config['userData'], config['leagues'][leagueName]["draft-turn"])
            
            return response[1] + f'Next player to draft is <@{user_id}>'
        else:
            draftOrder = draftBot.getDraftOrder()
            coachName = message.author.name
            draftOrderIndex = draftOrder.index(coachName)
            response = draftBot.draft(args[1], coachName, draftOrderIndex)
            return response[1]
                
    
    #---------------------------------- all further commands are admin commands
    if not message.author.guild_permissions.administrator:
        return 'You do not have permission to use this command'
    
    if '!initleague' == args[0]:            
        if len(args) != 2:
            return "Error: command must be in format: !initLeague <leagueName>\n\nNote <leagueName> must be one word without parentheses"
        
        if str(channelId) in config['channelData']:
            return "Error: current channel already in use"
        
        if args[1] in config['leagues']:
            return f"Error: a league with the name {args[1]} already exists"
        
        config['channelData'][channelId] = {
            'leagueName': args[1],
            'type': 'admin',
            'channelName': message.channel.name
        }
        config['leagues'][args[1]] = DEFAULT_LEAUGE_CONFIG
        
        saveConfig(CONFIG_FILE_NAME, config)
            
        return f"Successfully created leauge {args[1]}"
    
    if not (channelId in config['channelData'] and config["channelData"][channelId]['type'] == 'admin'):
        return "Please use admin commands in an admin channel"
    
    
    
    if '!setdraftorder' == args[0]:
        order = draftBot.setRandomDraftOrder()
        config['leagues'][leagueName]['draft-turn'] = order[0]
        saveConfig(CONFIG_FILE_NAME, config)
        
        msg = "Draft order is: \n"
        for user in order:
            msg += f"- {user}\n"
        return msg        
    
    if '!setcoach' == args[0]:
        if len(args) != 4:
            return "Error: must be in format !setCoach <user> <role> <acr>"
        if len(args[3]) > 4:
            return "Acroynm must be 4 characters or less"
        if len(message.role_mentions) != 1 or len(message.mentions) != 1:
            return "Please @mention the user and team role of the coach"
        
        maxCoaches = config['leagues'][leagueName]["num-coaches"]
        if config['leagues'][leagueName]["player-count"] <= maxCoaches:
            return "Error: already at max number of coaches"
        
        user = message.mentions[0]
        role = message.role_mentions[0]
        
        if user.id not in config['userData']:                           # case: never been in any league
            config['userData'][user.id] = {
                'username': user.name,
                'leagues': {
                    leagueName: {
                        'roleId': role.id,
                        'acronym': args[3]
                    }
                }
            }
            config['leagues'][leagueName]['num-coaches'] += 1
            saveConfig(CONFIG_FILE_NAME, config)
            draftBot.setCoach(user.name, role.name, args[3])
            return f"Added {user.name} to {leagueName}"
        
        elif leagueName not in config['userData'][user.id]['leagues']:  # case: been a league but not this one
            config['userData'][user.id]['leagues'][leagueName] = {
                'roleId': role.id,
                'acronym': args[3]
            }
            config['leagues'][leagueName]['num-coaches'] += 1
            saveConfig(CONFIG_FILE_NAME, config)
            draftBot.setCoach(user.name, role.name, args[3])
            return f"Added {user.name} to {leagueName}"
        
        else:                                                           # case in: current league, update current values
            config['userData'][user.id]['leagues'][leagueName] = {
                'roleId': role.id,
                'acronym': args[3]
            }
            saveConfig(CONFIG_FILE_NAME, config)
            draftBot.setCoach(user.name, role.name, args[3])
            return f"Updated {user.name} data for {leagueName}"
    
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
            
            config['leagues'][leagueName]['sheet-id'] = args[2]
            saveConfig(CONFIG_FILE_NAME, config)

            return "Successfully set and connected to sheet"
        
        if args[1] == 'player-count':
            if not args[2].isnumeric():
                return "Failed to set player-count, value must be numeric"
            
            with open(CONFIG_FILE_NAME, 'r') as json_file:
                config = json.load(json_file)
            
            config['leagues'][leagueName]['player-count'] = int(args[2])
            
            saveConfig(CONFIG_FILE_NAME, config)
            return f"Successfully set player-count to {args[2]}"
        
        if args[1] == 'draft-enabled':
            if args[2].lower() != 'true' and args[2].lower() != 'false':
                return f'Error: invalid value for draft-enabled, must be "true" or "false"'
            
            with open(CONFIG_FILE_NAME, 'r') as json_file:
                config = json.load(json_file)
            
            config['leagues'][leagueName]['draft-enabled'] = bool(args[2])
            
            saveConfig(CONFIG_FILE_NAME, config)
            return f"Successfully set draft-enabled to {args[2]}"
        

    if args[0] == '!setchannel':
        if len(args) != 3:
            return "Error: must be in format !setChannel <#channel> <type>"
        
        if len(message.channel_mentions) != 1:
            return "Error: please #mention the channel you want to set"
        
        channel = message.channel_mentions[0]
        
        if channel.id in config['channelData']:
            return f'Error: channel has been set as an {config["channelData"][channel.id]["type"]}'
        
        if args[2].lower() == 'draft':
            config['channelData'][channel.id] = {
                'leagueName': leagueName,
                'type': 'draft',
                'channelName': channel.name
            }
            saveConfig(CONFIG_FILE_NAME, config)
            return f"Successfully set {channel.mention} to be a draft channel"
        else:
            return f"Error: unknown channel type '{args[2]}'"
        
        
def saveConfig(filename, configDict):
    with open(filename, 'w') as json_file:
        json.dump(configDict, json_file, indent=4)
        

def getIDByName(dataDict, name):
    for id, data in dataDict.items():
        if data.get('username') == name:
            return id
    return None