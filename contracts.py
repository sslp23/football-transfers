import pandas as pd
from tqdm import tqdm
import numpy as np

import requests
from bs4 import BeautifulSoup
import time
from io import StringIO
import sys

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

def find_contract_link(s, sns, league_code):

    splitted = s.split("/")

    team_name = splitted[4]

    if "fc" in team_name:
        new_team_name = team_name.split("-")[1]+"-"+team_name.split("-")[0]
    else:
        new_team_name = team_name


    return s.replace("/"+team_name, new_team_name).replace('startseite', 'berateruebersicht').split('saison_id')[0] + f"plus/1"

#all teams links
def get_links(league_code, seasons):
    base_link = f"https://www.transfermarkt.co.uk/championship/startseite/wettbewerb/{league_code}/plus/?saison_id="#2021
    base = "https://www.transfermarkt.co.uk/"
    
    all_urls = []
    for s in (seasons):
        url =f"https://www.transfermarkt.co.uk/championship/startseite/wettbewerb/{league_code}/plus/?saison_id="+str(s)
        print(url)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        
        team_links = soup.find_all("table", {"class": "items"})
        links = []

        for row in team_links[0].find("tbody").children:
            if row.name == "tr":
                cells = row.find("td", {"class": "hauptlink no-border-links"})
                new_url = (base+cells.find("a").get("href"))
                tn = cells.find("a").text.split(" FC")[0]
                right_url = find_contract_link(new_url, s, league_code)
                links+= [(tn, right_url)]
        all_urls += (links) 
    return all_urls

def get_contract_details(link):
    response = requests.get(link[1], headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    all_transfers = soup.find('table', {'class': 'items'}).find("tbody")
    all_teams_df = pd.DataFrame()

    infos = []
    #trs = soup.find_all('tr', class_=['odd', 'even'])
    
    for a in all_transfers.find_all('tr', class_=['odd', 'even']):
        position = a.find('td')['title']
        player_name = a.find('td', {'class': 'posrela'}).find_all('td')[1].find('a')['title']
        player_id = a.find('td', {'class': 'posrela'}).find_all('td')[1].find('a')['href'].split('/')[-1]
        age = a.find_all('td', {'class': 'zentriert'})[1].text
        nationality = a.find_all('td', {'class': 'zentriert'})[2].find('img')['title']
        joined = a.find_all('td', {'class': 'zentriert'})[3].text
        expires = a.find_all('td', {'class': 'zentriert'})[4].text
        option = a.find_all('td', {'class': 'zentriert'})[5].text
        last_extension = a.find_all('td', {'class': 'zentriert'})[6].text
        try:
            agent_id = a.find_all('td', {'class': 'rechts'})[0].find('a')['href'].split('/')[-1]
            agent = a.find_all('td', {'class': 'rechts'})[0].find('a').text
        except:
            agent_id = -1
            agent = ''

        new_df = pd.DataFrame([[position, player_name, player_id, age, nationality, joined, expires, option, last_extension, agent, agent_id]], 
                              columns=['Position', 'Player Name', 'Player_ID', 'Age', 'Nationality', 'Joined', 'Expires', 'Option', 'Last Extension', 'Agent', 'Agent_ID'])
        new_df
        all_teams_df = pd.concat([all_teams_df, new_df])

    all_teams_df['Team'] = [link[0]]*len(all_teams_df)
    all_teams_df['Team_ID'] = [link[1].split('/')[-3]]*len(all_teams_df)
    return all_teams_df

def main():
    seasons = np.arange(2024, 2025).tolist()
    mode = sys.argv[1]
    if mode == 'update':
        seasons = seasons[-1:]

    leagues = ['GB1', 'L1', 'PO1', 'FR1', 'IT1', 'ES1', 'TR1', 'TS1', 'NL1', 'BE1']

    base_df = pd.DataFrame()
    for l in leagues:
        print(f"getting {l} data from {seasons} - {mode} mode")
        team_links =get_links(l, seasons)
        tl = []
        for team in tqdm(team_links):
            passed = 0
            while passed == 0:
                try:
                    tl.append(get_contract_details(team))
                    passed = 1
                except:
                    print(f'team {team} error - trying again')
                    time.sleep(5)
        all_teams = pd.concat(tl)
        all_teams['League'] = [l]*len(all_teams)

        base_df = pd.concat([base_df, all_teams])
    
    if mode == 'update':
        old_df = pd.read_data('data/contract_agents_info.csv')
        old_df[old_df.Season != float(str(seasons[-1])+str(seasons[-1]+1)[-2:])]
        base_df = pd.concat([old_df, base_df])
    base_df.to_csv('data/contract_agents_info.csv', index=False)

if __name__=="__main__":
    main()