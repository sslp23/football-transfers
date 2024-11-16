import pandas as pd
from tqdm import tqdm
import numpy as np

import requests
from bs4 import BeautifulSoup
import time
import sys

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

def find_stats_link(s, sns, league_code):

    splitted = s.split("/")

    team_name = splitted[4]

    if "fc" in team_name:
        new_team_name = team_name.split("-")[1]+"-"+team_name.split("-")[0]
    else:
        new_team_name = team_name


    return s.replace("/"+team_name, new_team_name).replace('startseite', 'leistungsdaten').split('saison_id')[0] + f"plus/1?reldata={league_code}%26"+str(sns)

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
                right_url = find_stats_link(new_url, s, league_code)
                links+= [(tn, right_url)]
        all_urls += (links) 
    return all_urls

def parse_link_full(link, how='populate'):
    league_name = link.split('=')[1].split('%')[0]
    link = link.replace(league_name, '')
    if how == 'update':
        link = link.split('?')[0]
    return link

#stats from squad
def find_squad_stats(als, how='populate'):
    team = als[0]
    link = als[1]
    season = link[-4:] + "-" + str(int(link[-2:])+1)
    new_link = parse_link_full(link, how=how)
    url = new_link
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    if how == 'update':
        new_season = soup.find('div', {'class': 'inline-select'}).find('optgroup').text.split('\n')[1].split(' ')[1]
        new_season = '20'+new_season.split('/')[0]+'-'+new_season.split('/')[1]
        season = new_season

        
        #print(new_season, url)
    #time.sleep(30309)
    team_links = soup.find_all("table", {"class": "items"})
    links = []
    
    all_p = []
    for row in team_links[0].find("tbody").children:
        player = [season, team]
        if row.name == "tr":
            cells = row.find_all("td")
            for cell in cells:
                if cell.find("img"):
                    #nationality
                    
                    if cell.find("td", {"class": "hauptlink"}):
                        player_link =cell.find("td", {"class": "hauptlink"}).find("span", {"class": "hide-for-small"}).find("a")["href"]#[-1]["href"])
                        #print(player_link)
                        #a = 
                        
                             #cell.find("span", {"class": "hide-for-small"}).find("a")["href"]
                        player_link = "https://www.transfermarkt.co.uk" + player_link.replace("profil", "leistungsdatendetails")
                            #player_resp = requests.get(player_link, headers={'User-Agent': 'not found 404'})
                            #player_soup = BeautifulSoup(player_resp.content, "html.parser")
                            #try:
                            #    height = player_soup.find("span", {"itemprop":"height"}).text[:-1].strip().replace(",", ".")
                            #except:
                            #    height = ' '
                            #print(height)
                        player.append(player_link)
                        player.append(player_link.split('/')[-1])
                    
                    elif "posrela" in cell["class"] and "bilderrahmen-fixed" in cell.find("img")["class"]:
                        #print(cell)
                        #print(cell)
                        player.append("not loaned")
                        natts = [n["title"] for n in cell.find_all("img")]
                        #print(natts)
                        player.append(natts[0])

                    elif cell.find("span"):
                        #print(cell)
                        loan_checker = cell.find("span").find("a")["title"]
                        
                        if "On loan from" in loan_checker:
                            player.append(loan_checker)
                        else:
                            player.append("not loaned")
                        player.append(cell.find("tr").find("a").find("img")["title"])
                elif cell.find("a"):
                    #print(cell.find("a")["title"])
                    player.append(cell.find('a')['title'])
                    
                else:
                    player.append(cell.text)

            

            all_p.append(player)
            
    all_p_df = pd.DataFrame(all_p, columns=["Season", "Team", "#", "Link" , 'PLAYER_ID', "Player Name", "Position", "Age", "Appearences", "Played Games", "Goals", "Assists", "Yellow", "Second Yellow", "Red", "Come From Bench", "Substituted", "PPG", "Minute Played"])
    
    for c in all_p_df.columns.values[7:]:#[7:]:
        all_p_df[c] = all_p_df[c].replace("Not in squad during this season", "0")
        all_p_df[c] = all_p_df[c].replace("Not used during this season", "0")
        all_p_df[c] = all_p_df[c].replace("-", "0")
        
        if all_p_df[c].dtype == object:
            all_p_df[c] = all_p_df[c].str.replace("'", "")
            #all_p_df[c] = all_p_df[c].str.replace(",", ".")
            if c=='Minute Played':
                all_p_df[c] = all_p_df[c].str.replace(".", "",regex=True)

            all_p_df[c] = all_p_df[c].str.replace("-", "")
            all_p_df[c] = all_p_df[c].str.replace("†", "")
        
        try:
            all_p_df[c] = all_p_df[c].astype(float)
        except:
            all_p_df[c] = all_p_df[c]
    
    all_p_df['TEAM_ID'] = link.split('/')[-3]
    return all_p_df

def main():
    #seasons -> from 2013 / 2024
    #if running in mode update, it will get only the last season data
    seasons = np.arange(2017, 2025).tolist()

    #python squads.py update
    #python squads.py populate -> default
    mode = sys.argv[1]
    if mode == 'update':
        seasons = seasons[-1:]
        
    leagues = ['GB1', 'L1', 'PO1', 'FR1', 'IT1', 'ES1', 'TR1', 'NL1', 'BE1', 'TS1', 'GB2', 'SER1', 'BRA1', 'AR1N', 'DK1']
    base_df = pd.DataFrame()
    for l in leagues:
        print(f"getting {l} data from {seasons} - {mode} mode")
        team_links =get_links(l, seasons)
        tl = []
        for team in tqdm(team_links):
            passed = 0
            while passed == 0:
                try:
                    tl.append(find_squad_stats(team, how=mode))
                    passed = 1
                except:
                    print(f'team {team} error - trying again')
                    time.sleep(5)
        all_teams = pd.concat(tl)
        all_teams['League'] = [l]*len(all_teams)

        base_df = pd.concat([base_df, all_teams])

    if mode == 'update':
        new_season = base_df.Season.values[-1]
        old_df = pd.read_csv('data/players_infos.csv')
        old_df = old_df[~((old_df.Season == new_season) & (old_df.League.isin(leagues)))]
        base_df = pd.concat([old_df, base_df])
    
    if mode == 'new_leagues':
        old_df = pd.read_csv('data/players_infos.csv')
        #old_df = old_df[old_df.Season != float(str(seasons[-1])+str(seasons[-1]+1)[-2:])]
        base_df = pd.concat([old_df, base_df])
    base_df.to_csv('data/players_infos.csv', index=False)

if __name__=="__main__":
    main()
    