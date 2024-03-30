from random import choice, randint
from sheets import DraftLeagueSheets

def get_response(userInput: str, draftBot: DraftLeagueSheets) -> str:
    lowered = userInput.lower()
    
    if lowered == '':
        return "no message"
    
    
    args = lowered.split(" ")
    args = [arg for arg in args if arg != ""]
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