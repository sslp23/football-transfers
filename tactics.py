import pandas as pd
from tqdm import tqdm
import requests
import sys

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

def get_tactical_systems(season, team_id, team, league):
    season_id = str(season)[:4]
    link = f'https://www.transfermarkt.co.uk/team/spielplan/verein/{team_id}/saison_id/{season_id}/plus/1'
    response = requests.get(link, headers=headers)
        
    games_df = pd.DataFrame()
    for df in pd.read_html(response.content):
        if 'System of play' in df.columns.values.tolist():
            games_df = pd.concat([games_df, df])
    
    system_df = games_df.groupby('Coach')['System of play'].agg(pd.Series.mode).to_frame('Most Used System').reset_index()
    system_df['Season'] = [season]*len(system_df)
    system_df['Team'] = [team]*len(system_df)
    system_df['Team_ID'] = [team_id]*len(system_df)
    
    total_games = games_df.groupby('Coach').size().to_frame('Games Used').reset_index()
    system_df = system_df.merge(total_games, how='left', on='Coach')

    return system_df

def main():
    df = pd.read_csv('data/players_infos.csv')

    target_teams = df[['Season', 'TEAM_ID', 'Team', 'League']].drop_duplicates()

    how = sys.argv[1]
    cur_season = '2024-25'

    if how == 'update':
        target_teams = target_teams[target_teams.Season == cur_season]

    tqdm.pandas()
    systems_df = target_teams.progress_apply(lambda x: get_tactical_systems(x['Season'], x['TEAM_ID'], x['Team'], x['League']), axis=1)
    pd.concat(systems_df.values.tolist()).to_csv('tactical_systems.csv', index=False)


if __name__ == "__main__":
    main()