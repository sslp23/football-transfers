import pandas as pd
from tqdm import tqdm
import numpy as np

import requests
from bs4 import BeautifulSoup
import time
from io import StringIO
import sys
headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

def parse_transfer_table(team_in, left=False):
    trs = team_in.find('tbody').find_all('tr')

    infos = []
    for tr in trs:
        try:
            player_name = tr.find('a')['title']
        except:
            if not left:
                return pd.DataFrame(infos, columns = ['PLAYER_NAME', 'PLAYER_ID', 'AGE', 'NATIONALITY', 'POSITION', 'MARKET_VALUE_ON_TRANSFER', 'TEAM_LEFT', 'TEAM_LEFT_ID', 'FEE'])
            else:
                return pd.DataFrame(infos, columns = ['PLAYER_NAME', 'PLAYER_ID', 'AGE', 'NATIONALITY', 'POSITION', 'MARKET_VALUE_ON_TRANSFER', 'TEAM_JOINED', 'TEAM_JOINED_ID', 'FEE'])

        player_id = tr.find('a')['href'].split('/')[-1]
        age = tr.find('td', {'class': 'zentriert alter-transfer-cell'}).text
        nat = tr.find('td', {'class': 'zentriert nat-transfer-cell'}).find('img')['title']
        pos = tr.find('td', {'class': 'pos-transfer-cell'}).text
        market_value = tr.find('td', {'class': 'rechts mw-transfer-cell'}).text
        try:
            team_left = tr.find('td', {'class': 'no-border-links verein-flagge-transfer-cell'}).find('a')['title']
        except:
            team_left = tr.find('td', {'class': 'no-border-links verein-flagge-transfer-cell'}).text
        
        try:
            team_left_id = tr.find('td', {'class': 'no-border-links verein-flagge-transfer-cell'}).find('a')['href'].split('/')[-3]
        except:
            team_left_id = np.nan
            
        fee = tr.find_all('td', {'class': 'rechts'})[-1].text
        all_infos = (player_name, player_id, age, nat, pos, market_value, team_left, team_left_id, fee)
        infos.append(all_infos)
    
    if not left:
        infos_df = pd.DataFrame(infos, columns = ['PLAYER_NAME', 'PLAYER_ID', 'AGE', 'NATIONALITY', 'POSITION', 'MARKET_VALUE_ON_TRANSFER', 'TEAM_LEFT', 'TEAM_LEFT_ID', 'FEE'])
    else:
        infos_df = pd.DataFrame(infos, columns = ['PLAYER_NAME', 'PLAYER_ID', 'AGE', 'NATIONALITY', 'POSITION', 'MARKET_VALUE_ON_TRANSFER', 'TEAM_JOINED', 'TEAM_JOINED_ID', 'FEE'])
    return infos_df 

def get_transfer(league_code, seasons):
    base_link = f'https://www.transfermarkt.co.uk/premier-league/transfers/wettbewerb/{league_code}/plus/?saison_id='

    seasons_df = pd.DataFrame()
    for s in (seasons):
        full_link = base_link+str(s)+'&s_w=&leihe=3&intern=0&intern=1'
        print(full_link)
        passed = False
        while not passed:
            response = requests.get(full_link, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            try:
                all_transfers = soup.find('div', {'class': 'large-8 columns'}).find_all("div", {"class": "box"})[3:]
                passed = True
            except:
                passed = False
                print('trying again...')
                time.sleep(5)
        all_teams_df = pd.DataFrame()
        
        for transf in all_transfers:
            
            team_id = transf.find('a')['href'].split('/')[-3]
            team_name = transf.find('a')['title']
            
            team_in, team_out = transf.find_all('table')[0], transf.find_all('table')[1]#pd.read_html(StringIO(str(transf.find_all('table')[0])))[0], pd.read_html(StringIO(str(transf.find_all('table')[0])))[0]
            team_in_df = parse_transfer_table(team_in)
            team_out_df = parse_transfer_table(team_out, left=True)

            team_out_df['TEAM_LEFT_ID'] = [team_id]*len(team_out_df)
            team_out_df['TEAM_LEFT'] = [team_name]*len(team_out_df)
            
            team_in_df['TEAM_JOINED_ID'] = [team_id]*len(team_in_df)
            team_in_df['TEAM_JOINED'] = [team_name]*len(team_in_df)
            team_df = pd.concat([team_in_df, team_out_df]).reset_index(drop=True)
            all_teams_df = pd.concat([all_teams_df, team_df])
            
        season_name = float(str(s)+str(s+1)[-2:])
        all_teams_df['SEASON'] = [season_name]*len(all_teams_df)
        seasons_df = pd.concat([seasons_df, all_teams_df])
    return all_teams_df
            

def main():
    seasons = np.arange(2017, 2025).tolist()    

    mode = sys.argv[1]
    if mode == 'update':
        seasons = seasons[-1:]

    leagues = ['GB1', 'L1', 'FR1', 'ES1', 'PO1', 'TR1', 'TS1', 'NL1', 'BE1', 'IT1']

    leagues_df = pd.DataFrame()
    for l in tqdm(leagues):
        a = get_transfer(l, seasons)
        leagues_df = pd.concat([leagues_df, a])
        
    if mode == 'update':
        old_df = pd.read_data('data/full_transfers.csv')
        old_df[old_df.SEASON != float(str(seasons[-1])+str(seasons[-1]+1)[-2:])]
        base_df = pd.concat([old_df, base_df])
    leagues_df.to_csv('data/full_transfers.csv', index=False)

if __name__ == "__main__":
    main()