import gspread
from google.oauth2 import service_account
import pandas as pd
import streamlit as st
import numpy as np
from squads import *
from contracts import *
from tactics import *
from transfers import *

scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
json_file = "credentials-api.json"
# Access GCP service account secrets
gcp_secrets = (st.secrets["gcp_service_account"]['gcp_info'])

def reader(spreadsheet_name):
    credentials = service_account.Credentials.from_service_account_info(gcp_secrets)
    scoped_credentials = credentials.with_scopes(scopes)
    gc = gspread.authorize(scoped_credentials)
    spreadsheet = gc.open(spreadsheet_name)
    
    tab = spreadsheet.worksheet(spreadsheet_name)
    data = tab.get_all_records()
    df = pd.DataFrame(data)
    return df

def writer(spreadsheet_name, df):
    credentials = service_account.Credentials.from_service_account_info(gcp_secrets)
    scoped_credentials = credentials.with_scopes(scopes)
    gc = gspread.authorize(scoped_credentials)
    spreadsheet = gc.open(spreadsheet_name)
    
    tab = spreadsheet.worksheet(spreadsheet_name)

    values = [df.columns.tolist()] + df.values.tolist()
    tab.clear()
    tab.update(values)

def update_transfers():
    seasons = np.arange(2017, 2025).tolist()    

    mode = 'update'
    if mode == 'update':
        seasons = seasons[-1:]

    leagues = ['GB1', 'L1', 'FR1', 'ES1', 'PO1', 'TR1', 'TS1', 'NL1', 'BE1', 'IT1']

    leagues_df = pd.DataFrame()
    for l in tqdm(leagues):
        a = get_transfer(l, seasons, mode)
        leagues_df = pd.concat([leagues_df, a])
        
    if mode == 'update':
        old_df = reader('full_transfers')#pd.read_csv('data/full_transfers.csv')
        
        new_season = leagues_df.SEASON.values[-1]
        old_df = old_df[~((old_df.SEASON == new_season))]
        leagues_df = pd.concat([old_df, leagues_df])
    
    writer('full_transfers', leagues_df.fillna(''))
    #leagues_df.to_csv('data/full_transfers.csv', index=False)

def update_tactics():
    df = reader('players_infos')
    target_teams = df[['Season', 'TEAM_ID', 'Team', 'League']].drop_duplicates()
    leagues = ['GB1', 'L1', 'FR1', 'ES1', 'PO1', 'TR1', 'TS1', 'NL1', 'BE1', 'IT1']
    target_teams = target_teams[target_teams.League.isin(leagues)]

    how = 'update'
    cur_season = '2024-25'

    if how == 'update':
        cur_season = target_teams[target_teams.League == 'GB1'].sort_values('Season').Season.values[-1]
        print(cur_season)
        target_teams = target_teams[target_teams.Season == cur_season]
        old_teams = reader('tactical_systems')

    tqdm.pandas()
    systems_df = target_teams.progress_apply(lambda x: get_tactical_systems(x['Season'], x['TEAM_ID'], x['Team'], x['League']), axis=1)
    if how == 'update':
        new_systems = pd.concat(systems_df.values.tolist())
        #print(new_systems)
        full_systems = pd.concat([old_teams, new_systems])
        full_systems['Most Used System'] = full_systems['Most Used System'].apply(lambda x: str(x))
        writer('tactical_systems', full_systems.fillna(''))

def update_contracts():
    seasons = np.arange(2024, 2025).tolist()
    mode = 'update'
    leagues = ['GB1', 'L1', 'PO1', 'FR1', 'IT1', 'ES1', 'TR1', 'TS1', 'NL1', 'BE1']

    base_df = pd.DataFrame()
    for l in leagues:
        print(f"getting {l} data from {seasons} - {mode} mode")
        team_links =get_links_contracts(l, seasons)
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
    writer('contract_agents_info', base_df.fillna(''))
    #base_df.to_csv('data/contract_agents_info.csv', index=False)

def update_squads():
    seasons = np.arange(2017, 2025).tolist()

    #python squads.py update
    #python squads.py populate -> default
    mode = "update"
    
    seasons = seasons[-1:]

    leagues = ['GB2', 'SER1', 'BRA1', 'AR1N', 'DK1', 'GB1', 'L1', 'PO1', 'FR1', 'IT1', 'ES1', 'TR1', 'NL1', 'BE1', 'TS1']
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

    new_season = base_df.Season.values[-1]
    old_df = reader('players_infos')
    old_df = old_df[~((old_df.Season == new_season) & (old_df.League.isin(leagues)))]
    base_df = pd.concat([old_df, base_df])
    writer('players_infos', base_df.fillna(''))
    #
    #base_df.to_csv('data/players_infos.csv', index=False)