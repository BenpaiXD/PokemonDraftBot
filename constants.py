CONFIG_FILE_NAME = 'config.json'

CONFIG_PARAMS = {'sheet-id', 'player-count'}

DEFAULT_LEAUGE = {
    "sheet-id": None,
    "player-count": 14,
    "draft-enabled": True,
    "draft-turn-id": 14,
    "budget": 120,
    "data-sheet": {
        "sheet-name": "Data",
        "coach-table-range": [
            "B",
            "E"
        ],
        "drafted-row-start": 2,
        "drafted-col-range": "BA:BB"
    },
    "draft-sheet": {
        "sheet-name": "Draft",
        "draft-order-col": "D",
        "draft-order-row-1": 4,
        "card-width": 8,
        "cards-start": 8,
        "card-top": 7,
        "card-height": 18
    },
    "dex-sheet": {
        "sheet-name": "Pok\u00e9dex",
        "data-range": "B:G"
    },
}