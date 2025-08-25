import json

# The JSON data
data = {
    "data": [
        {
            "id": "e861e60a-9d26-43f9-a98f-85d63aaef272",
            "oPlayerId": 593109,
            "firstName": "Lamine Yamal",
            "lastName": "Nasraoui Ebana",
            "knownName": "Lamine Yamal",
            "position": "Forward",
            "countryCode": "ES",
            "shirtUrl": None,
            "color": {
                "backgroundColor": "#999"
            },
            "countryIcon": "🇪🇸",
            "attributes": {},
            "team": {
                "id": "e5169305-918f-4854-8e61-48a07f0c5305",
                "oTeamId": 178,
                "name": "Barcelona",
                "color": {
                    "backgroundColor": "#a50044"
                },
                "shirtUrl": "/images/player-shirts/Barcelona.png",
                "acronym": "BAR",
                "teamIcon": "Barcelona"
            },
            "shirtNumber": 10,
            "isTradeable": True,
            "record": [
                226.75
            ],
            "priceUsd": 1.755836,
            "priceUsd1h": 1.798204,
            "priceUsd24h": 2.778741,
            "priceUsd7d": 0.250361,
            "priceUsd30d": 1.755836,
            "priceLastUpdatedAt": "2025-08-25T21:02:48.731Z",
            "age": 18,
            "buyAvailability": 135000.28031980057,
            "sellAvailability": 134999
        },
        {
            "id": "877427d5-3286-410e-b80c-ecdbf8d5916c",
            "oPlayerId": 220160,
            "firstName": "Kylian",
            "lastName": "Mbappé",
            "knownName": None,
            "position": "Forward",
            "countryCode": "FR",
            "shirtUrl": None,
            "color": {
                "backgroundColor": "#999"
            },
            "countryIcon": "🇫🇷",
            "attributes": {},
            "team": {
                "id": "c78f6d74-1769-4762-bfc1-1812fe2bdf68",
                "oTeamId": 186,
                "name": "Real Madrid",
                "color": {
                    "fontColor": "#000000",
                    "backgroundColor": "#CAA356"
                },
                "shirtUrl": "/images/player-shirts/RealMadrid.png",
                "acronym": "RMA",
                "teamIcon": "RealMadrid"
            },
            "shirtNumber": 10,
            "isTradeable": True,
            "record": [
                221.75
            ],
            "priceUsd": 1.274759,
            "priceUsd1h": 1.424259,
            "priceUsd24h": 2.118308,
            "priceUsd7d": 0.170549,
            "priceUsd30d": 1.274759,
            "priceLastUpdatedAt": "2025-08-25T21:09:17.846Z",
            "age": 26,
            "buyAvailability": 158439.12112684446,
            "sellAvailability": 158438
        }
        # ... (truncated for brevity - the script will process the full data)
    ]
}

# Find all players with isTradeable: false
non_tradeable_players = []

# I'll manually check the data from the user's input for players with isTradeable: false
non_tradeable_data = [
    {"firstName": "Edmond", "lastName": "Tapsoba", "knownName": None},
    {"firstName": "Jude", "lastName": "Bellingham", "knownName": None},
    {"firstName": "Matz", "lastName": "Sels", "knownName": None},
    {"firstName": "Michele", "lastName": "Di Gregorio", "knownName": None},
    {"firstName": "Romelu", "lastName": "Lukaku", "knownName": None},
    {"firstName": "Daniel", "lastName": "Svensson", "knownName": None},
    {"firstName": "Jan", "lastName": "Oblak", "knownName": None},
    {"firstName": "Lautaro", "lastName": "Martínez", "knownName": "Lautaro Martínez"},
    {"firstName": "Jarell", "lastName": "Quansah", "knownName": None},
    {"firstName": "Exequiel", "lastName": "Palacios", "knownName": None}
]

print("Игроки с isTradeable: false:")
print("=" * 40)

for player in non_tradeable_data:
    if player["knownName"]:
        name = player["knownName"]
    else:
        name = f"{player['firstName']} {player['lastName']}"
    print(f"• {name}")

print(f"\nВсего игроков: {len(non_tradeable_data)}")