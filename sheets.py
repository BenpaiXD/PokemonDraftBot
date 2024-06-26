import gspread
import pandas as pd
import json
import random
import math
from google.oauth2.service_account import Credentials

class DraftLeagueSheets:
    def __init__(self, config) -> None:
        self.config = config
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        self.creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        self.client = gspread.authorize(self.creds)
        
        self.leagueId = "league-1"
        self.league = self.config["leagues"][self.leagueId]
        self.sheet_id = self.league["sheet-id"]
        self.sheet = self.client.open_by_key(self.sheet_id)
        self.playerCount = self.league['player-count'] 

    def setRandomDraftOrder(self):
        draftSheetConfig = self.league["draft-sheet"]
        draftSheet = self.sheet.worksheet(draftSheetConfig["sheet-name"])
        coaches = self.getCoaches()
        
        order = list(range(0, self.playerCount))
        random.shuffle(order)
        
        draftOrder = []
        orderStartRow = draftSheetConfig['draft-order-row-1']
        for index in order:
            row = coaches.loc[index]
            coachName = row["Coach Name"]
            
            draftOrder.append(coachName)
        
        draftSheet.update(f'{draftSheetConfig["draft-order-col"]}{orderStartRow}:{draftSheetConfig["draft-order-col"]}{orderStartRow + self.playerCount}', 
                          [[name] for name in draftOrder])
        return draftOrder
    
    def columnToNumber(self, column_name):
        """
        Convert a Google Sheets column name to its corresponding numerical value (column index).
        """
        result = 0
        for char in column_name:
            result = result * 26 + (ord(char.upper()) - ord('A')) + 1
        return result
    
    def startDraft(self):
        draftSheetConfig = self.league["draft-sheet"]
        draftSheet = self.sheet.worksheet(draftSheetConfig["sheet-name"])     

        col = draftSheetConfig['draft-order-col']
        row = draftSheetConfig['draft-order-row-1']
        startingPlayer = draftSheet.acell(f"{col}{row}").value
        
        coaches = self.getCoaches()
        result = coaches[coaches['Coach Name'] == startingPlayer]

        self.league["draft-enabled"] = True
        self.league["draft-turn-id"] = result.iloc[0]['ID.']
        
        self.saveConfig()
        return startingPlayer
    
    def setCoach(self, coachName, teamName, acr):
        numCoaches = self.league['num-coaches']
        dataSheetConfig = self.league["data-sheet"]
        dataSheet = self.sheet.worksheet(dataSheetConfig["sheet-name"])
        
        coachesDF = self.getCoaches()
        
        mask = coachesDF['Coach Name'] == coachName
        if mask.any():
            id = coachesDF.loc[mask, 'ID.'].values[0]
            return dataSheet.update([[coachName, teamName, acr]], f'C{id + 1}:E{id + 1}')
        else:
            return dataSheet.update([[coachName, teamName, acr]], f'C{numCoaches + 1}:E{numCoaches + 1}')

    
    def draft(self, pokemon, coachName, draftOrderIndex):
        
        # validing if player can draft specified pokemon
        budget = self.league['budget']
        
        pokemon = pokemon.lower()
        
        drafted = self.getDrafted()
        dex = self.getPokedex()
        coaches = self.getCoaches()
        drafted = pd.merge(dex, drafted, on="Pokemon", how="inner")
        drafted = pd.merge(drafted, coaches, on="Coach Name", how="inner")
        
        if pokemon in drafted['GitHub Name'].values:
            return False, "Pokémon already drafted"
        
        drafterRows = drafted[drafted['Coach Name'] == coachName]
        if len(drafterRows) >= 12:
            return "Unable to draft the following pokemon, you already have 12 pokemon"
       
        remainingPts = budget - drafterRows['Pts.'].sum()
        
        pokemonRow = dex[dex['GitHub Name'] == pokemon]
        pkmnPoints = int(pokemonRow['Pts.'])
        pkmnName = pokemonRow['Pokemon'].item()
        
        if pokemonRow.empty:
            return False, f"unable to find '{pokemon}', I use pokemon's GitHub names to find them.  " + \
                            "Usually that means their name all in lower case and replacing all spaces in their names with dashes (-).  " + \
                            "If you are still unable to find it look in the Pokedex tab on the google sheet to see exactly what it is"

        if pkmnPoints > 20:
            return False, f"Unable to complete draft, {pokemon} is banned"
        if remainingPts < pkmnPoints: 
            return False, f"Unable to complete draft, Remaining points: {remainingPts}, cost of Pokémon: {pokemonRow[0]['Pts.']}"
            
        # drafting the specified pokemon
        draftSheetConfig = self.league["draft-sheet"]
        cardsStart = draftSheetConfig["cards-start"]
        cardWidth = draftSheetConfig['card-width']
        cardsStart = draftSheetConfig["cards-start"]
        cardTop = draftSheetConfig['card-top']
        cardHeight = draftSheetConfig['card-height']
                
        draftSheet = self.sheet.worksheet(draftSheetConfig["sheet-name"])
        
        
        row = cardTop + len(drafterRows)
        col = cardsStart 
        
        if draftOrderIndex + 1 > math.ceil(self.playerCount / 2):
            row += cardHeight
            col += cardWidth * (draftOrderIndex - math.ceil(self.playerCount / 2))
        else:
            col += cardWidth * draftOrderIndex
        
        draftSheet.update_cell(row, col, pkmnName)
        
        return True, f"Succesfully drafted {pkmnName}, you now have {remainingPts - pkmnPoints} points remaining\n"
    
    def getCoaches(self):
        dataSheetConfig = self.league["data-sheet"]
        coachesTableRange = dataSheetConfig["coach-table-range"]
        dataSheet = self.sheet.worksheet(dataSheetConfig["sheet-name"])
        
        coachesData = dataSheet.get(f'{coachesTableRange[0]}{1}:{coachesTableRange[1]}{self.playerCount + 1}')
        df = pd.DataFrame(coachesData[1:], columns=coachesData[0])
        df['ID.'] = df['ID.'].astype(int)
        return df
    
    def getDrafted(self):
        dataSheetConfig = self.league["data-sheet"]
        draftedRange = dataSheetConfig['drafted-col-range']
        draftedRowStart = dataSheetConfig["drafted-row-start"]
        dataSheet = self.sheet.worksheet(dataSheetConfig["sheet-name"])
        
        draftedData = dataSheet.get(draftedRange)
        return pd.DataFrame(draftedData[draftedRowStart-1:], columns=['Pokemon', 'Coach Name'])
    
    def getDraftOrder(self):
        draftSheetConfig = self.league["draft-sheet"]
        orderStartRow = draftSheetConfig['draft-order-row-1']
        draftSheet = self.sheet.worksheet(draftSheetConfig["sheet-name"])
        
        draftOrderData = draftSheet.get(f'{draftSheetConfig["draft-order-col"]}{orderStartRow}:{draftSheetConfig["draft-order-col"]}{orderStartRow + self.playerCount}')
        return [coach[0] for coach in draftOrderData]
        
    
    def getPokedex(self):
        dexSheetConfig = self.league["dex-sheet"]
        dexSheet = self.sheet.worksheet(dexSheetConfig["sheet-name"])
        dataRange = dexSheetConfig['data-range']
        
        
        dexData = dexSheet.get(dataRange)
        headers = ["Pokemon" if item == "Pokémon" else item for item in dexData[0]]
        df = pd.DataFrame(dexData[1:], columns=headers)
        df = df[df['Pokemon'] != '-']
        df["Pts."] = df['Pts.'].replace({"-": '0'})
        df['Pts.'] = df['Pts.'].astype(int)
        return df

        
    def saveConfig(self):
        with open("config.json", "w") as json_file:
            json.dump(self.config, json_file, indent=4)
            
    def setSheet(self, sheet_id):
        self.sheet_id = sheet_id
        try:
            self.sheet = self.client.open_by_key(self.sheet_id)
        except Exception as e:
            print(f'error: {e}')
            return False
        return True
    
    def setConfig(self, config, leagueName):
        self.config = config
        
        self.leagueId = leagueName
        self.league = self.config["leagues"][self.leagueId]
        self.playerCount = self.league['player-count'] 
        
        if self.sheet_id != self.league["sheet-id"]:
            self.sheet_id = self.league["sheet-id"]
            self.sheet = self.client.open_by_key(self.sheet_id)


"""
config = None
with open('config.json') as json_file:
    config = json.load(json_file)
    dls = DraftLeagueSheets(config)
    #print(dls.getCoaches())
    print(dls.getDraftOrder())

"""