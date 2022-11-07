#%%
from espn_api.basketball import League
import pandas as pd
from datetime import datetime, date, timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_table
import pickle
import dash_loading_spinners as dls
import numpy as np
year = 2023
week = 4
league_id = 18927521
X_test = pd.read_csv('data/X_df.csv').set_index(["Name",'Week',"Tm"])
y_df = pd.read_csv('data/y_df.csv').set_index(['Name','Week',"Tm"])
model_gp = pickle.load(open('models/OLS_weekly_model_fp_final.sav', 'rb'))

league = League(league_id=league_id,year=year)
matchups = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")
matchups_list = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")[0]
#%%
team_dict = pd.read_excel("data/nba-2022-EasternStandardTime.xlsx",sheet_name='Sheet1')
team_dict = team_dict.set_index('Teams').to_dict()['Abr']
schedule = pd.read_excel("data/nba-2022-EasternStandardTime.xlsx",sheet_name='in')
schedule = schedule.replace(team_dict)

week = int(week)
matchup = matchups.index(matchups_list)

start_date = datetime(2022,10,18)+timedelta((week-1)*7)-timedelta(1)
end_date = start_date+timedelta(7)

schedule['Date']= schedule['Date'].apply(pd.to_datetime,dayfirst=True)
schedule = schedule[schedule['Date']>=start_date]
schedule = schedule[schedule['Date']<end_date]
schedule_df = pd.concat([schedule.groupby("Away Team").count()['Match Number'],schedule.groupby("Home Team").count()['Match Number']],axis=1)
schedule_df = schedule_df.fillna(0)
games_this_week = schedule_df['Match Number'].sum(axis=1)


home_team = league.scoreboard(week)[matchup].home_team
away_team = league.scoreboard(week)[matchup].away_team

away_score = league.scoreboard(week)[matchup].away_final_score
home_score = league.scoreboard(week)[matchup].home_final_score

if date.today().weekday() == 0:
    use_last_weeks_lineup = 1
else:
    use_last_weeks_lineup = 0

away_players = league.box_scores(week-use_last_weeks_lineup)[matchup].away_lineup
home_players = league.box_scores(week-use_last_weeks_lineup)[matchup].home_lineup
df2 = pd.DataFrame(data=[[str(home_team).split("(")[1][:-1],home_score,0,str(away_team).split("(")[1][:-1],away_score,0]],columns=['Home Team','Home Score','Home Predicted Score','Away Team','Away Score','Away Predicted Score'])
for i in range(min(len(home_players),len(away_players))):
    name_filter = X_test[X_test.index.get_level_values("Name")==str(home_players[i]).split(',')[0].split('(')[1]+'  ']
    date_filter = name_filter[name_filter.index.get_level_values("Week")==float(week)-2]
    if date_filter.empty:
        if not name_filter.empty:
            tm = name_filter.index.get_level_values('Tm').values[0]
            mean_points = np.mean(name_filter['FPoints'])
            predicted_home = mean_points*games_this_week[tm]
        else:
            predicted_home=0
    else:
        date_filter['Games_next_week']=games_this_week[name_filter.index.get_level_values('Tm')].values[0]
        predicted_home = model_gp.predict(date_filter).round(0).values[0]

    name_filter = X_test[X_test.index.get_level_values("Name")==str(away_players[i]).split(',')[0].split('(')[1]+'  ']
    date_filter = name_filter[name_filter.index.get_level_values("Week")==float(week)-2]
    if date_filter.empty:
        if not name_filter.empty:
            tm = name_filter.index.get_level_values('Tm').values[0]
            mean_points = np.mean(name_filter['FPoints'])
            predicted_away = mean_points*games_this_week[tm]
        else:
            predicted_away=0
    else:
        date_filter['Games_next_week']=games_this_week[name_filter.index.get_level_values('Tm').values[0]]
        predicted_away = model_gp.predict(date_filter).round(0).values[0]
    if datetime.today()<start_date:
        df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(0.0),'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(0.0),'Away Predicted Score':round(predicted_away,2)},ignore_index=True)
    else:
        df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(home_players[i]).split(',')[1].split(':')[1][:-1],'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(away_players[i]).split(',')[1].split(':')[1][:-1],'Away Predicted Score':round(predicted_away,2)},ignore_index=True)

df2['Home Predicted Score'][0] = df2['Home Predicted Score'][1:].sum().round(0)
df2['Away Predicted Score'][0] = df2['Away Predicted Score'][1:].sum().round(0)
# %%
