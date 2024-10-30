import streamlit as st
import pandas as pd

if __name__=='__main__':
    # Load the data
    df = pd.read_csv('../data/players_infos.csv')

    # Configure the dashboard
    st.set_page_config(page_title="Transfers Overview", page_icon="⚽", layout="centered")

    # Title
    st.title("Transfers Overview")

    df['Season'] = df.Season.astype(int).astype(str)
    df.Season = df.Season.apply(lambda x: x[:4]+'-'+x[4:])
    # Sidebar filters
    season = st.sidebar.selectbox("Select Season", df['Season'].unique())
    team = st.sidebar.selectbox("Select Team", df[df['Season'] == season]['Team'].unique())

    # Filter the dataframe
    filtered_df = df[(df['Season'] == season) & (df['Team'] == team)]

    # Display the filtered dataframe
    st.dataframe(filtered_df)
