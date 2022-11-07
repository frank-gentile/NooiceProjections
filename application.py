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
league_id = 18927521

league = League(league_id=league_id,year=year)
#model = pickle.load(open('OLS_model.sav', 'rb'))

model_gp = pickle.load(open('models/OLS_weekly_model_fp_final.sav', 'rb'))

X_test = pd.read_csv('data/X_df.csv').set_index(["Name",'Week',"Tm"])
y_df = pd.read_csv('data/y_df.csv').set_index(['Name','Week',"Tm"])



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
application = app.server
app.title = 'Nooice Projections'
suppress_callback_exceptions=True

app.layout = dbc.Container([
        html.Br(),
        dbc.Row(dbc.Col(html.H1("Nooice Forecasting Tool (NFT)"),width={'size':'auto'}),align='center',justify='center'),
        html.Br(),
        dcc.Tabs([dcc.Tab(label='Fantasy Projections', children = [
            dbc.Row(dbc.Col(html.H6(
            '''Projections below are from a model trained on 2021 NBA data and forecasted using previous weeks stats.
            '''
        ),width=12,align='center'),align='center',justify='center'),



        html.Br(),
        dbc.Row([
            dbc.Col([
                html.Label('Week = '),
                dcc.Dropdown(id='week',
                 options=[{'label': i, 'value': i} for i in range(2,18)],
                        multi=False,
                        value=2,
                        style={'width': "60%"}
                        )]),

            dbc.Col([
                html.Label('Matchup = '),
                dcc.Dropdown(id='matchups_list',
                        multi=False,
                        style={'width': "60%"}
                        ),
                        ],width={'size':9}),
            ],align='center',justify='center'),

        # dbc.Row([
        #     dbc.Col([
        #         dbc.Button('Update', id='submit-val', n_clicks=0,color='primary')
        #     ])
        # ]),

        html.Br(),
        html.Br(),

        dbc.Row(dbc.Col(dls.Hash(html.Div(id='update_table'),color="#435278",
                        speed_multiplier=2,
                        size=100)),justify='center',align='center'),

        html.Br(),
        html.Br(),

        ]), 
        dcc.Tab(label='Individual Projections', children = [
            html.Br(),
            html.Label("Coming Soon!")
            # html.Br(),
            # dbc.Row([
            #     dbc.Col(
            #         [html.Label("Date =  "),
            #             dcc.DatePickerSingle(
            #                 id='my-date-picker-single',
            #                 min_date_allowed=datetime(2022,10,18),
            #                 max_date_allowed=datetime(year,4,1),
            #                 date='2022-10-20'
            #                 )]),
            #     dbc.Col(
            #         [html.Label('Category = '),
            #         dcc.Dropdown(id='category',
            #         options=[{"label":"Points","value":"Points"},
            #                 {"label":"Rebounds","value":"Rebounds"},
            #                 {"label":"Assists","value":"Assists"}],
            #                 multi=False,
            #                 value="Points",
            #                 style={'width': "60%"}
            #                 )])
            #                 ]),
            # html.Br(),
            #         dbc.Row(dbc.Col(dls.Hash(html.Div(id='update_cat_table'),color="#435278",
            #             speed_multiplier=2,
            #             size=100)),justify='center',align='center'),

                
  
        ]

        )
 ])
])

    
@app.callback([Output('matchups_list','options')],
                [Input('week','value')])
def update_matchup_list(week):
    matchup_list = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")
    return [[{'label': i, 'value': i} for i in matchup_list]]
@app.callback([Output('matchups_list','value')],
               [Input('matchups_list','options')])
def set_matchup_list(matchup):
    return [matchup[0]['value']]


@app.callback([
               Output("update_table", "children"),
               ],
      [Input('matchups_list','value'),
      Input('week','value')])
def getPic(matchups_list,week):
    league_id = 18927521

    league = League(league_id=league_id,year=year)
    matchups = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")

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

    if datetime.today().date()==start_date.date():
        if date.today().weekday() == 0:
            use_last_weeks_lineup = 1
        else:
            use_last_weeks_lineup = 0
    else:
        use_last_weeks_lineup=0

    away_players = league.box_scores(week-use_last_weeks_lineup)[matchup].away_lineup
    home_players = league.box_scores(week-use_last_weeks_lineup)[matchup].home_lineup
    if use_last_weeks_lineup:
        df2 = pd.DataFrame(data=[[str(home_team).split("(")[1][:-1],0,0,str(away_team).split("(")[1][:-1],0,0]],columns=['Home Team','Home Score','Home Predicted Score','Away Team','Away Score','Away Predicted Score'])
    else:
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
            date_filter['Games_next_week']=games_this_week[name_filter.index.get_level_values('Tm').values[0]]
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
            if use_last_weeks_lineup:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(0.0),'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(0.0),'Away Predicted Score':round(predicted_away,2)},ignore_index=True)
            else:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(home_players[i]).split(',')[1].split(':')[1][:-1],'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(away_players[i]).split(',')[1].split(':')[1][:-1],'Away Predicted Score':round(predicted_away,2)},ignore_index=True)

    df2['Home Predicted Score'][0] = df2['Home Predicted Score'][1:].sum().round(0)
    df2['Away Predicted Score'][0] = df2['Away Predicted Score'][1:].sum().round(0)

    df2 = df2.astype(str)

    table = html.Div(
        [
            dash_table.DataTable(
                data=df2.to_dict("rows"),
                columns=[{"id": x, "name": x} for x in df2.columns],
                            style_table={'display': 'block', 'max-width': '600px', 'border': '2px grey',
                                            },
                                style_as_list_view=True,
                                style_header={
                                    'backgroundColor': '#e1e4eb',
                                    'fontWeight': 'bold',
                                    'align': 'center'
                                },
                                style_cell={
                                    # all three widths are needed
                                    'fontSize': '18', 'font-family': 'sans-serif', 'font-color': 'grey',
                                    'minWidth': '30px', 'width': '300px', 'maxWidth': '600px',
                                    'overflow': 'hidden',
                                    'textOverflow': 'ellipsis',
                                    'textAlign': 'center', },)
        ]
    )


    return [table]


# @app.callback([
#                Output("update_cat_table", "children"),
#                ],
#       [Input('my-date-picker-single','date'),
#       Input('category','value')])

# def getCatTable(date,category):
#     cat_dict = {'Points':'pts','Rebounds':'reb','Assists':'ast'}
#     y_df_dict = {'Points':'PTS','Rebounds':'TRB','Assists':'AST'}
#     X_test = pd.read_csv('data/'+cat_dict[category]+'.csv').set_index(['Date','Opp','Name'])
#     X_test = X_test[X_test.index.get_level_values('Date')==date]

    
#     model_gp_cat = pickle.load(open('models/finalized_model_'+cat_dict[category]+'.sav', 'rb'))

#     df2 = model_gp_cat.predict(X_test)
#     df2 = df2.reset_index()


#     y_df = pd.read_excel('data/y_df2022.xlsx')


#     df2 = pd.merge(df2,y_df[['Date','Opp','Name',y_df_dict[category]]],on=['Date','Opp','Name'])


#     df2[0] = df2[0].astype(int)

#     df2 = df2.sort_values(by=[0],ascending=False)

#     df2 = df2.rename(columns={0:'Projection'})


#     table = html.Div(
#         [
#             dash_table.DataTable(
#                 data=df2.to_dict("rows"),
#                 columns=[{"id": str(x), "name": str(x)} for x in df2.columns],
#                             style_table={'display': 'block', 'max-width': '600px', 'border': '2px grey',
#                                             },
#                                 style_as_list_view=True,
#                                 style_header={
#                                     'backgroundColor': '#e1e4eb',
#                                     'fontWeight': 'bold',
#                                     'align': 'center'
#                                 },
#                                 style_cell={
#                                     # all three widths are needed
#                                     'fontSize': '18', 'font-family': 'sans-serif', 'font-color': 'grey',
#                                     'minWidth': '30px', 'width': '300px', 'maxWidth': '600px',
#                                     'overflow': 'hidden',
#                                     'textOverflow': 'ellipsis',
#                                     'textAlign': 'center', },)
#         ]
#     )



#     return [table]

if __name__ == '__main__':
    app.run_server(debug=True)

# %%
