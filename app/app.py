import streamlit as st
import pandas as pd
from tqdm import tqdm

import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.patches import Rectangle
from io import BytesIO
import plotly.express as px

def heatmap_maker(ideal):
    
    # Set up the pitch with a white background and no padding
    pitch = Pitch(
        pitch_type='statsbomb', 
        pitch_color='white', 
        line_color='grey', 
        line_zorder=1,  # Pitch lines appear above the grid
        pad_top=0, 
        pad_bottom=0, 
        pad_left=0, 
        pad_right=0
    )
    fig, ax = pitch.draw(figsize=(10, 7))

    # Define grid dimensions
    num_rows, num_cols = 5, 6
    pitch_length, pitch_width = 120, 80

    df_pos = pd.DataFrame([('GK', [(3, 1)]), ('CB', [(2, 2), (3, 2), (4, 2)]), ('RB', [(5, 2)]), ('LB', [(1, 2)]), ('DM', [(2, 3), (3, 3), (4, 3)]), ('CM', [(2, 4), (3, 4), (4, 4)]), ('LM', []), ('RM', []), ('RW', [(5, 5), (5, 4)]), ('LW', [(1, 4), (1, 5)]), ('ST', [(2, 5), (3, 5), (4, 5), (2, 6), (3, 6), (4, 6)])], columns = ['Position', 'Local'])

    # Plot vertical and horizontal lines to create a 5x6 grid with light grey lines
    for i in range(1, num_rows):
        pitch.lines(0, i * 80 / num_rows, 120, i * 80 / num_rows, lw=2, color="lightgrey", ax=ax)
    for j in range(1, num_cols):
        pitch.lines(j * 120 / num_cols, 0, j * 120 / num_cols, 80, lw=2, color="lightgrey", ax=ax)

    df_pos = df_pos.merge(ideal[['Position', 'Difference']], how='left', on='Position')
    # Display the pitch with the customized grid
    for i, vals in df_pos.iterrows():
        for local in vals['Local']:
            zone_row, zone_col = local[0], local[1]
            zone_center_x = (zone_col - 0.5) * (pitch_length / num_cols)
            zone_center_y = (zone_row - 0.5) * (pitch_width / num_rows)
            ax.text(zone_center_x, zone_center_y, vals['Position'], ha="center", va="center", fontsize=14, color="black")
            
            if vals['Difference']<0:
                color = 'red'
            elif vals['Difference']>0:
                color = 'green'
            else:
                color = 'white'
            zone_x = (zone_col - 1) * (pitch_length / num_cols)  # Left edge of the zone
            zone_y = (zone_row - 1) * (pitch_width / num_rows)   # Bottom edge of the zone
            zone_width = pitch_length / num_cols
            zone_height = pitch_width / num_rows
            ax.add_patch(Rectangle((zone_x, zone_y), zone_width, zone_height, color=color, alpha=0.3, zorder=0))

    return fig


def find_cap(s):
    pos = ''.join([char for char in s if char.isupper()])
    if pos == 'G':
        pos = 'GK'
    return pos

def get_team_info(df, team, season):
    tactics = pd.read_csv('../data/tactical_systems.csv')
    
    teams_df = df[['Season', 'TEAM_ID', 'Team', 'League']]
    
    #tactics['Season'] = tactics.Season.astype(int).astype(str)
    #tactics.Season = tactics.Season.apply(lambda x: x[:4]+'-'+x[4:])

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
    for i, vals in (teams_df_info.iterrows()):
        sub_df = df[(df.TEAM_ID == vals['TEAM_ID']) & (df.Season ==  vals['Season'])]
        
        res_df = pd.pivot_table(sub_df.groupby('POS_CODE').size().to_frame('current_pos_count').reset_index(), columns = 'POS_CODE', values='current_pos_count')
        res_df.columns = [a+'_current' for a in res_df.columns]
        res_df['TEAM_ID'] = vals['TEAM_ID']
        res_df['Season'] = vals['Season']
        
        res_df_full = pd.concat([res_df_full, res_df])

    res_df_full = res_df_full.fillna(0)

    teams_df_info = teams_df_info.merge(res_df_full, how='left', on=['TEAM_ID', 'Season'])
    return teams_df_info

def transfer_type(x):
    if 'loan transfer' in x or 'Loan fee' in x:
        return 'Loan'
    elif 'free transfer' in x:
        return 'Free'
    else:
        return 'Paid'

def get_htb(position, team, season):
    transfers = pd.read_csv('../data/full_transfers.csv')
    transfers['POS_CODE'] = transfers.POSITION.apply(lambda x: find_cap(x))
    transfers.POS_CODE = transfers.POS_CODE.str.replace('CF', 'ST').str.replace('SS', 'ST')
    transfers.POS_CODE = transfers.POS_CODE.str.replace('AM', 'CM')
    transfers = transfers[~transfers.POS_CODE.isin(['A', 'D', 'M'])]

    #season = float(season[:4]+season[5:])

    int_transfer = transfers[(transfers.SEASON <= season) & (transfers.TEAM_JOINED_ID == team) & (transfers.POS_CODE == position)]
    
    sel_transfer = int_transfer[['PLAYER_NAME', 'AGE', 'FEE', 'POS_CODE', 'SEASON']].sort_values('SEASON')
    sel_transfer = sel_transfer[~sel_transfer.FEE.str.contains('End of loan')].drop_duplicates().reset_index(drop=True)
    sel_transfer = sel_transfer[sel_transfer.FEE!= '-']
    sel_transfer['TRANSFER_TYPE'] = sel_transfer.FEE.apply(lambda x: transfer_type(x))
    return sel_transfer

def htb_donut_chart(htb):
    transfer_summary = htb.groupby('TRANSFER_TYPE').agg(
            Count=('TRANSFER_TYPE', 'size'),
            Players=('PLAYER_NAME', lambda names: ',<br>'.join(
                f"{name} ({season})" for name, season in zip(names, htb.loc[names.index, 'SEASON'])
            ))
        ).reset_index()

    total_transfers = transfer_summary['Count'].sum()

    fig = px.pie(
        transfer_summary,
        names='TRANSFER_TYPE',
        values='Count',
        hole=0.4  # Adjust the size of the inner white circle (0.4 for 40% hole)
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Transfers: %{value}<br>Players: %{customdata[0]}",
        customdata=transfer_summary[['Players']].values  # Pass player names as custom data
    )

    # Customize the chart layout
    fig.update_layout(
        title="Transfer Type Distribution",
        showlegend=True,
        annotations=[
        dict(
            text=f"{total_transfers}<br>Transfers",  # Display total and label
            x=0.5, y=0.5,
            font_size=20, showarrow=False
        )
        ]
    )
    return fig

def render_img_html(image_b64):
        st.markdown(f"<img style='max-width: 100%;max-height: 100%;' src='data:image/png;base64, {image_b64}'/>",
                    unsafe_allow_html=True)


if __name__=='__main__':
    # Load the data
    df = pd.read_csv('../data/players_infos.csv')

    # Configure the dashboard
    st.set_page_config(page_title="Transfers Overview", page_icon="⚽", layout="wide")

    # Title
    st.sidebar.title("Transfers Overview")

    #df['Season'] = df.Season.astype(int).astype(str)
    #df.Season = df.Season.apply(lambda x: x[:4]+'-'+x[4:])
    # Sidebar filters
    leagues_dict = {
        'GB1': 'Premier League',
        'L1': 'Bundesliga',
        'PO1': 'Primeira Liga',
        'FR1': 'Ligue 1',
        'IT1': 'Serie A',
        'ES1': 'La Liga',
        'TR1': 'Süper Lig',
        'NL1': 'Eredivisie',
        'BE1': 'Jupiler Pro League',
        'TS1': 'Czech League'
    }
    df['League'] = df['League'].replace(leagues_dict)
    season = st.sidebar.selectbox("Select Season", df['Season'].unique().tolist()[::-1])
    league = st.sidebar.selectbox("Select League", df[df['Season'] == season]['League'].unique())
    team = st.sidebar.selectbox("Select Team", df[(df['Season'] == season) & (df['League'] == league)]['Team'].unique())
    #option = st.sidebar.selectbox("Select Option", ["ideal", "current", "difference"])

    teams_df_info = get_team_info(df, team=team, season=season)
    team_id = teams_df_info.TEAM_ID.values[-1]
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
    final_df['Difference'] = final_df['Current'] - final_df['Ideal']
    
    hmap = heatmap_maker(final_df.reset_index())
    #backup_df = backup_df[(backup_df.Team == team) & (backup_df.Season == season)]
    # Filter the dataframe
    #filtered_df = df[(df['Season'] == season) & (df['Team'] == team)]

    # Display the filtered dataframe
    
    #st.subheader("Squad Stats")
    st.markdown(f"<h2 style='text-align: center;'>{team} - {season}</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(final_df)
    with col2:
        buf = BytesIO()
        hmap.savefig(buf, format="png")
        buf.seek(0)
        st.image(buf, caption="Position's heatmap")

    st.markdown(f"<h2 style='text-align: center;'>Historical Transfers Behavior</h2>", unsafe_allow_html=True)
    position = st.selectbox('Position', df.POS_CODE.unique())

    htb = get_htb(position, team_id, season)
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(htb)
    with col2:
        fig = htb_donut_chart(htb)
        st.plotly_chart(fig, use_container_width=True)
    #team = st.sidebar.selectbox("Select Team", df[(df['Season'] == season) & (df['League'] == league)]['Team'].unique())
