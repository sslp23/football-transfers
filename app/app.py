import streamlit as st
import pandas as pd
from tqdm import tqdm

def find_cap(s):
    pos = ''.join([char for char in s if char.isupper()])
    if pos == 'G':
        pos = 'GK'
    return pos

def get_team_info(df, team, season):
    tactics = pd.read_csv('../data/tactical_systems copy.csv')
    
    teams_df = df[['Season', 'TEAM_ID', 'Team', 'League']]
    
    tactics['Season'] = tactics.Season.astype(int).astype(str)
    tactics.Season = tactics.Season.apply(lambda x: x[:4]+'-'+x[4:])

    teams_df = teams_df.merge(tactics[['Coach', 'Most Used System', 'Season', 'Team_ID']], how='left', left_on=['Season', 'TEAM_ID'], right_on=['Season', 'Team_ID']).drop('Team_ID', axis=1)

    teams_df_train = teams_df[(teams_df.Season == season) & (teams_df.Team == team)]#[teams_df.Season>'201718']
    teams_df_train = (teams_df_train.drop_duplicates())
    ly_tactics = []
    for i, vals in tqdm(teams_df_train.iterrows()):
        last_year_info = teams_df_train[(teams_df_train.Season == vals['Season']) & (teams_df_train.TEAM_ID == vals['TEAM_ID'])]
        if len(last_year_info)>0:
            
            last_year_tactics = last_year_info['Most Used System'].tail(1).values[0]
        else:
            last_year_tactics = vals['Most Used System']
        ly_tactics.append(last_year_tactics)
    
    teams_df_train['LAST_YEAR_TACTICS'] = ly_tactics
    tactics_pos = pd.read_csv('../data/Target Score Chart - MPT.csv')
    tactics_pos = tactics_pos.iloc[:, 1:]
    tactics_pos.columns = [a.strip() for a in tactics_pos.iloc[0].values] 
    tactics_pos = tactics_pos.iloc[1:]

    tactics_pos['Formation'] = tactics_pos.Formation.str.split(' ').str[0]
    tactics_df = pd.pivot_table(tactics_pos, index='Formation', columns='Position', values='Ideal Number')
    cor_order = ['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'LM', 'RM', 'RW', 'LW', 'ST']
    tactics_df = tactics_df[cor_order]

    tactics_df = tactics_df.reset_index()

    new_tactics = pd.DataFrame([['3-4-2-1', 3, 5, 2, 2, 2, 4, 0, 0, 2, 2, 2],
        ['4-1-4-1', 3, 4, 2, 2, 2, 4, 0, 0, 2, 2, 2]], columns=tactics_df.columns)

    tactics_df = pd.concat([tactics_df, new_tactics], axis=0)
    teams_df_train['LAST_YEAR_TACTICS'] = [str(a).split("'")[-2] if '[' in a else a for a in teams_df_train['LAST_YEAR_TACTICS'].values]
    teams_df_train['LAST_YEAR_TACTICS'] = teams_df_train['LAST_YEAR_TACTICS'].str.split(' ').str[0]

    tactics_df.columns = [a+'_ideal' if len(a) == 2 else a for a in tactics_df.columns.values]

    teams_df_info = teams_df_train.merge(tactics_df, how='left', left_on = 'LAST_YEAR_TACTICS', right_on = 'Formation', suffixes=['', '_ideal'])
    
    df['POS_CODE'] = df.Position.apply(lambda x: find_cap(x))
    df.POS_CODE = df.POS_CODE.str.replace('CF', 'ST').str.replace('SS', 'ST')
    df.POS_CODE = df.POS_CODE.str.replace('AM', 'CM')
    df = df[~df.POS_CODE.isin(['A', 'D', 'M'])]

    res_df_full = pd.DataFrame()
    for i, vals in tqdm(teams_df_info.iterrows()):
        sub_df = df[(df.TEAM_ID == vals['TEAM_ID']) & (df.Season ==  vals['Season'])]
        
        res_df = pd.pivot_table(sub_df.groupby('POS_CODE').size().to_frame('current_pos_count').reset_index(), columns = 'POS_CODE', values='current_pos_count')
        res_df.columns = [a+'_current' for a in res_df.columns]
        res_df['TEAM_ID'] = vals['TEAM_ID']
        res_df['Season'] = vals['Season']
        
        res_df_full = pd.concat([res_df_full, res_df])

    res_df_full = res_df_full.fillna(0)

    print(res_df_full)
    teams_df_info = teams_df_info.merge(res_df_full, how='left', on=['TEAM_ID', 'Season'])
    return teams_df_info

if __name__=='__main__':
    # Load the data
    df = pd.read_csv('../data/players_infos.csv')

    # Configure the dashboard
    st.set_page_config(page_title="Transfers Overview", page_icon="⚽", layout="wide")

    # Title
    st.sidebar.title("Transfers Overview")

    df['Season'] = df.Season.astype(int).astype(str)
    df.Season = df.Season.apply(lambda x: x[:4]+'-'+x[4:])
    # Sidebar filters
    season = st.sidebar.selectbox("Select Season", df['Season'].unique().tolist()[::-1])
    team = st.sidebar.selectbox("Select Team", df[df['Season'] == season]['Team'].unique())
    #option = st.sidebar.selectbox("Select Option", ["ideal", "current", "difference"])

    teams_df_info = get_team_info(df, team=team, season=season)
    base_cols = ['Season', 'Team']
    backup_df = teams_df_info[(teams_df_info.Team == team) & (teams_df_info.Season == season)]

    ideal_cols = [a for a in backup_df if '_ideal' in a ]
    current_cols = [a for a in backup_df if '_current' in a ]
    
    positions_ideal = [a.split('_')[0] for a in ideal_cols]
    df_ideal = backup_df[ideal_cols].T.reset_index()
    df_ideal['positions'] = positions_ideal

    positions_current = [a.split('_')[0] for a in current_cols]
    df_current = backup_df[current_cols].T.reset_index()
    df_current['positions'] = positions_current
    final_df = df_ideal.merge(df_current, how='left', on='positions')
    
    
    final_df = final_df.fillna(0)
    final_df = final_df.iloc[:,[0, 1, -1]]
    final_df.columns = ['Position', 'Ideal', 'Current']
    final_df['Team'] = [team]*len(final_df)
    final_df['Season'] = [season]*len(final_df)
    final_df['Position'] = [a.split('_')[0] for a in final_df.Position]

    final_df = final_df[['Ideal', 'Current', 'Team', 'Season', 'Position']].set_index('Position')
    #backup_df = backup_df[(backup_df.Team == team) & (backup_df.Season == season)]
    # Filter the dataframe
    #filtered_df = df[(df['Season'] == season) & (df['Team'] == team)]

    # Display the filtered dataframe
    
    st.subheader("Squad Stats")
    st.dataframe(final_df)
