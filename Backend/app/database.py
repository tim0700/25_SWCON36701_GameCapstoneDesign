import sqlite3
import json

# Insert generated character sheet at database
def InsertCharacterSheetinDatabase(json_file: str):

    # Create a database connection
    connection = sqlite3.connect('../Assets/StreamingAssets/StaticDB.db')
    cursor = connection.cursor()
    
    # Load character sheet JSON data from file
    json_data = json_file
    
    # Parse JSON data
    npc_id = json_data.get('npc_id')
    name = json_data.get('name')
    age = json_data.get('age')
    gender = json_data.get('gender')
    role = json_data.get('role_title')
    faction = json_data.get('faction')
    personality = json_data.get('psychological_profile').get('personality_keywords')
    personality = ', '.join(personality)
    speaking_style = json_data.get('psychological_profile').get('speaking_style')
    location = json_data.get('primary_location')

    print(f"Parsed NPC Data: {npc_id}, {name}, {age}, {gender}, {role}, {faction}, {personality}, {speaking_style}, {location}")
    
    # Insert parsed data into the NPC table
    insert_query = f"INSERT INTO NPC VALUES ('{npc_id}', '{name}', '{age}', '{gender}', '{role}', '{faction}', '{personality}', '{speaking_style}', '{location}')"
    cursor.execute(insert_query)

    # Commit changes and close the connection
    connection.commit()
    connection.close()
