#%%
import requests
import pandas as pd
import bs4 as bs
from formattingFuncs import getPlayerData, getTeams, formatLinks,getPlayersFromTeam, getFantasyPoints
import numpy as np


read_from_web_players = 0
read_from_web_teams = 0
lags=2
year = 2023

playerlist = pd.read_excel('data/NBA_players22.xlsx')['Player']
links_list = formatLinks(playerlist,year)
#%%

def getTeamData(link):
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.content,'lxml')
    tables = soup.findAll('table')
    html = resp.text
    soup = bs.BeautifulSoup(html, 'lxml')
    table = tables[-1]
    table_headers = []
    for tx in table.findAll('th'):
        if len(table_headers)>31:
            col_rename = tx.text+'o'
            table_headers.append(col_rename)
        else:
            table_headers.append(tx.text)

        if len(table_headers)==36:
            break
    for j in ['Advanced','Offensive Four Factors','Defensive Four Factors','Rk']:
        table_headers.remove(j)
    table_headers = list(filter(None, table_headers))
    
    team_data = pd.DataFrame(data=None, columns = table_headers)
        
    if table.findParent("table") is None:
        for row in table.findAll('tr')[1:]:
            line = []
            for obs in row.findAll('td'):
                dummy = obs.text
                line.append(dummy)

            if len(line) == len(table_headers):
                df2 = pd.DataFrame(line).T
                df2.columns = table_headers
                team_data = team_data.append(df2)
    team_data = team_data.reset_index()
    team_data = team_data.drop(['index'],axis=1)
    team_data = team_data.drop(team_data.columns[3],axis=1)
    team_data = team_data.drop('\xa0',axis=1)
    team_data.loc[:,'ORtg':] = team_data.loc[:,'ORtg':].astype(float)
    team_data['Team'] = link[43:46]
    return team_data

def getPlayerDataAdv(link):
    link = link[:-5]+'-advanced'+link[-5:]
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.content,'lxml')
    tables = soup.findAll('table')
    table = tables[-1]
    table_headers = []
    for tx in table.findAll('th'):
        table_headers.append(tx.text)
        if len(table_headers)==24:
            break
    table_headers.pop(0)
    player_data = pd.DataFrame(data=None, columns = table_headers)
        
    if table.findParent("table") is None:
        for row in table.findAll('tr')[1:]:
            line = []
            for obs in row.findAll('td'):
                dummy = obs.text
                line.append(dummy)
                if line[-1]=="Did Not Play" or line[-1]=='Inactive' or line[-1]=='Did Not Dress':
                    pass
                    # zeroes = [0]*len(table_headers)
                    # zeroes[:len(line)-1] = line[:-1]
                    # #zeroes[0]=len(player_data)+1
                    # [str(i) for i in zeroes]
                    # df2 = pd.DataFrame(zeroes).T
                    # df2.columns = table_headers
                    # player_data = player_data.append(df2)

            if len(line) == len(table_headers):
                df2 = pd.DataFrame(line).T
                df2.columns = table_headers
                player_data = pd.concat([player_data,df2])
    player_data = player_data.reset_index()
    player_data = player_data.drop(['index'],axis=1)
    player_data = player_data.drop(player_data.columns[3],axis=1)
    player_data_col_list = list(player_data.columns)
    player_data_col_list[3] = 'At'
    player_data_col_list[5] = 'W/L'
    player_data.columns = player_data_col_list
    player_data['Name'] = str(soup.find_all('title')[0]).split('|')[0][7:].replace("2022-23 Advanced Game Log","")
    return player_data


if read_from_web_players:
    player_df = pd.DataFrame()
    y_df = pd.DataFrame()
    total_player_df_summed = pd.DataFrame()
    for link in links_list:
        basic_player_data, pic = getPlayerData(link)
        if type(basic_player_data) == pd.core.frame.DataFrame:
            if not basic_player_data.empty:
                adv_player_data = getPlayerDataAdv(link)
                player_data_joined = basic_player_data.merge(adv_player_data,on=['G','Date','Age','At','Opp','W/L','GS','MP'])
                player_data_joined = player_data_joined.set_index(['G','Date','Age','Opp','W/L','At','Name','Tm'])
                for i in range(len(player_data_joined)):
                    if player_data_joined['MP'][i] != 0:
                        player_data_joined['MP'][i] = (float(player_data_joined['MP'][i].split(':')[0])*60+float(player_data_joined['MP'][i].split(':')[1]))/60
                player_data_joined = player_data_joined.replace('',0)
                player_data_joined = player_data_joined.astype(float)
                player_data_joined = player_data_joined.drop(['FG%','3P%','FT%','GmSc_x'],axis=1)

                df_lagged = pd.DataFrame()

                for window in range(1, lags+1):
                    shifted = player_data_joined.shift(window)
                    shifted.columns = [x + "_lag" + str(window) for x in player_data_joined.columns]
                    df_lagged = pd.concat((df_lagged, shifted), axis=1)
                    if window == 1:
                        cum_avg = player_data_joined.expanding().mean()
                        cum_avg.columns = [x + "_avg" for x in player_data_joined.columns]
                        df_lagged = pd.concat((df_lagged, cum_avg), axis=1)
                df_lagged = df_lagged.dropna()
                total_player_df = pd.concat([player_df,df_lagged])
                player_data_joined = player_data_joined[lags:]
                total_player_df_summed = pd.concat([total_player_df_summed,total_player_df])
                y_df = pd.concat([y_df,player_data_joined])




    total_player_df_summed.to_csv('data/total_player_df'+str(year)+'.csv')
    y_df.to_csv('data/y_df'+str(year)+'.csv')



team_abbr = list(pd.read_excel('data/teams.xlsx',sheet_name='Sheet2')['Teams'])
big_team_df = pd.DataFrame()

if read_from_web_teams:
    for tm in team_abbr:
        link_tm = 'https://www.basketball-reference.com/teams/'+tm+'/'+str(year)+'/gamelog-advanced/'
        tm_data = getTeamData(link_tm)
        tm_data = tm_data.set_index(['G','Date','W/L','Team'])
        df_lagged = pd.DataFrame()

        for window in range(1, lags+1):
            shifted = tm_data.shift(window)
            shifted.columns = [x + "_lag" + str(window) for x in tm_data.columns]
            df_lagged = pd.concat((df_lagged, shifted), axis=1)
        tm_data = df_lagged.dropna()
        big_team_df = big_team_df.append(tm_data)
    big_team_df.to_csv('data/big_team_df'+str(year)+'.csv')