#IMPORT STATEMENTS
import sys
import pandas as pd
import requests 
from bs4 import BeautifulSoup
import folium

#THIS CALLS ANOTHER gmapskey.py file where I'm storing the google maps key that is used later down the code.  
import gmapskey

#GLOBAL VARIABLES
base_url = "https://maps.googleapis.com/maps/api/geocode/json?"

#FUNCTION THAT PASSES AN ADDRESS TO RETURN A LAT, LONG FROM GOOGLE MAPS API.  
#NOTE IT PASSES THE KEY FROM THE gmapskey file THAT IS NOT SAVED HERE BUT IN A SEPERATE FILE.  
def getLocation(address):
    params={
         "key": gmapskey.gmapskey,
         "address": address
    }
    response = requests.get(base_url, params = params).json()
    print(response.keys())
    if response ["status"] == "OK":
         geometry = response["results"][0]["geometry"]
         longitude = geometry["location"]["lng"]
         latitude = geometry["location"]["lat"]
    return f"{longitude}" + "," + f"{latitude }"  

#START A BEATIFUL SOUP REQUEST TO THE ESPN SOCCER SCHEDULE PAGE
url = "https://www.espn.com/soccer/schedule"
page = requests.get(url)
soup = BeautifulSoup(page.text, "html.parser")

#LOOK FOR SPECIFIC CLASSES OF ROWS.  THESE TEND TO CHANGE FREQUENTLY ENOUGH THAT CODE MAY BREAK IN THE FUTURE ON THESE LINES OF CODE.  
#THIS IS A KEY PIECE OF CODE THAT GENERATES A RESULT SET WITH THE NAMES
games = soup.find_all('tr', attrs = {'class': 'Table__TR Table__TR--sm Table__even'})

#CREATE A PANDAS DATAFRAME TO POPULATE THE GAMES DATASET INTO FOR FURTHER PROCESSING.  
final_df = pd.DataFrame()

#LOOP THROUGH GAMES RESULTS SET AND POPULATE THE FINAL DATAFRAME.
#MAY BE A MORE EFFICIENT WAY OF DOING THIS BUT FOUND SOMETHING THAT WORKED AND RAN WITH IT.  
for game in games:
    
    results = [result.get_text() for result in game.find_all('td')]
    
    temp_df = pd.DataFrame(results).transpose()
    
    final_df = pd.concat([final_df, temp_df], ignore_index=True)
    
#for testing only get first 3 rows
#final_df = final_df.head(1)

#ASSUME THAT THE NAME OF THE LOCATION IS UNDER THE 2ND OR 3RD COLUMN.
#THIS IS NEEDED BECAUSE IF THE GAME HAS BEEN FINISHED, IT MOVES INTO ANOTHER COLUMN
#ANOTHER AREA THAT COULD PROBABLY BE MORE EFFICIENT.      
final_df.loc[final_df[3] != '', 'location']  = final_df[3] 
final_df.loc[final_df[3] == '', 'location']  = final_df[4] 

#CREATE A FILTERED DATA FRAME THAT ONLY CONTAINS ROWS THAT HAVE SOMETHING IN THE LOCATION FIELD.  
filter_df = final_df[final_df['location'] != '']

#FILTER DF FOR TESTING
#filter_df = filter_df.head(1)

#CALL THE getLocation() FUNCTION TO POPULATE THE LAT, LONG INTO ANOTHER COLUMN
filter_df["latlong"] = filter_df['location'].map(lambda a: getLocation(a))

#SPLIT OUT THE LAT, LONG AGAIN
filter_df[['lat', 'long']] = filter_df['latlong'].str.split(',', expand=True)

#CONVERT LAT AND LONG TO FLOATS SO WE CAN ADD IT TO THE MAP BELOW.
#THIS MAY BE ANOTHER AREA THAT COULD BE MORE EFFICIENT.  
filter_df['lat'] = filter_df['lat'].astype(float)
filter_df['long'] = filter_df['long'].astype(float)


#CREATE A FOLIM MAP SHOWING THE ENTIRE WORLD.  
m = folium.Map(location=[0, 0], zoom_start=2)

#LOOP THROUGH DATA FILTER AND ADD IT TO THE MAP.  
#filter_df.apply(lambda row:folium.Marker(location=[row["long"], row["lat"]], radius=10, popup=row["location"] + " " + row[0] + " " + row[1]).add_to(m), axis=1)

filter_df.apply(lambda row:folium.Marker(location=[row["long"], row["lat"]], radius=10,  icon=folium.Icon(color='red', icon=''), popup="<b> Location of Match: " + row["location"] +"</b><br/></br>" + row[0] + row[1] ).add_to(m), axis=1)


#FINALLY, SAVE THE FOLIUM MAP AS AN .HTML FILE.  
m.save('soccer_map.html')

filter_df_export  = filter_df[['location', 'lat', 'long']]

filter_df_export['location'] = filter_df_export['location'].str.replace(',','')

filter_df_export.to_csv('soccer_export.csv')


#m.save('mysite/templates/soccer_map.html')
 
    