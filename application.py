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
import create_plot
import plotly.express as px
import data_m



end_df = pd.read_csv('data/data2.csv')

#model = pickle.load(open('OLS_model.sav', 'rb'))

model_gp = pickle.load(open('models/OLS_weekly_model_fp_final.sav', 'rb'))

X_test = pd.read_csv('data/X_df.csv').set_index(["Name",'Week',"Tm"])
y_df = pd.read_csv('data/y_df.csv').set_index(['Name','Week',"Tm"])

animations = {'Scatter':px.scatter(end_df,x='FP_avg',y='mins_avg',color='team',animation_frame='G',size='Points accumulated',range_y=[10,48],range_x=[0,50],hover_name='Name', size_max=45
),'Bar':px.bar(end_df,x='team',y='Points accumulated',color='team',animation_frame='G',animation_group='Name',hover_name='Name',range_y=[0,5000])}


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
application = app.server
app.title = 'Nooice Projections'
suppress_callback_exceptions=True

app.layout = dbc.Container([
        html.Br(),
        dbc.Row(dbc.Col(html.H1("Nooice Forecasting Tool (NFT)"),width={'size':'auto'}),align='center',justify='center'),
        html.Br(),
        html.Label('League ID = '),
        dcc.Input(id='league_id',value=18927521),
        html.Br(),
        html.Label('Year = '),
        dcc.Input(id='year',value=2023),
        html.Br(),
        dbc.Button('Update', id='submit-val', n_clicks=0,color='primary'),
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
                        value=14,
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
        dbc.Row(dbc.Col(dls.Hash(html.Div(id='update_table2'),color="#435278",
                        speed_multiplier=2,
                        size=100)),justify='center',align='center'),

        ]), 
        dcc.Tab(label='League Analysis', children = [
            html.Br(),
            
    #dbc.Button('Update player data', id='submit-val', n_clicks=0,color='primary'),
        html.P('''The following graph contains player level fantasy data, showing the average fantasy points per game against minutes per game over time, with 
        the size of the points indicating the total fantasy points accumulated. '''),
        html.P("Select an animation:"),
        dcc.RadioItems(
            id='selection',
            options=[{'label': x, 'value': x} for x in animations],
            value='Scatter'
        ),
        dcc.Graph(id="graph"),
        html.P('''This Violin Plot shows the normalized distribution of weekly scores. 'Normalized' meaning your score for the week minus the 
        average score of your opponents. Wider violins indicate greater frequency of the range, while thinner violins greater variation in scores.
        Points on each plot are considered outliers'''),
        dcc.Graph(id="violin"),
        html.P('''This 'Luck Plot' describes the normalized 'points for' vs normalized 'points against' Each quadrant qualifies wins and losses
        as 'lucky' or 'unlucky' and 'good' or 'bad' '''),
        dcc.Graph(id="luck"),
        html.P('''This heatmap describes the p-value associated with a simple t-test with the null nypothesis that team2 > team1. For example, 
        if the underlying p-value is <0.05 you can safely reject the null and imply that team1 is better than team2. '''),   
        dcc.Graph(id="heat"),
        html.P('''Presented by Frunk Analytics LLC'''),   

        ])
    ])])
@app.callback(
    [Output("graph", "figure"),
    Output("violin", "figure"),
    Output("luck", "figure"),
    Output("heat","figure")], 
    [Input('submit-val','n_clicks'),
     Input("selection", "value")
     ],[State("league_id","value"),
        State('year','value')])
def display_animated_graph(n_clicks,s,league_id,year):
    league = League(league_id=int(league_id),year=int(year))

    if league_id == 18927521 and year==2023:
        df = pd.read_csv('data/df_analytics.csv')
        df_against = pd.read_csv('data/df_against_analytics.csv')
        df_joined = pd.read_csv('data/df_joined_analytics.csv')
        df_p = pd.read_csv('data/df_p_analytics.csv')
    else:
        scores = dict()
        scores_against = dict()

        scores, scores_against = data_m.findScores(league,scores,scores_against)

        df, df_against, df_joined = data_m.createDataFrame(scores,scores_against)
        df_p = data_m.CreatePValues(df_joined)
        
    fig = create_plot.getLuckSkillPlot(df,df_against)

    violin_fig = create_plot.getViolinPlots(df)

    heat_map = create_plot.PlotlyHeatmap(df_p)


    return animations[s], violin_fig, fig, heat_map

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

                
  

    
@app.callback([Output('matchups_list','options')],
                [Input('submit-val','n_clicks'),
                 Input('week','value')
                 ],[State("league_id","value"),
                    State('year','value')])
def update_matchup_list(n_clicks,week,league_id,year):
    league = League(league_id=int(league_id),year=int(year))
    matchup_list = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")
    return [[{'label': i, 'value': i} for i in matchup_list]]
@app.callback([Output('matchups_list','value')],
               [Input('submit-val','n_clicks'),
                Input('matchups_list','options')
                ])
def set_matchup_list(n_clicks,matchup):
    return [matchup[0]['value']]


@app.callback([
               Output("update_table", "children"),
               Output("update_table2", "children"),
               ],
      [Input('submit-val','n_clicks'),
       Input('matchups_list','value'),
      Input('week','value')
      ],[State("league_id","value"),
        State('year','value')])
def getPic(n_clicks,matchups_list,week,league_id,year):

    league = League(league_id=int(league_id),year=int(year))
    matchups = str(league.scoreboard(week)).replace("Matchup","").replace("Team","").replace("(","").replace(")),","*").replace(")","").replace("[","").replace("]","").split("*")

    team_dict = pd.read_csv("data/abr.csv")
    team_dict = team_dict.set_index('Teams').to_dict()['Abr']
    schedule = pd.read_csv("data/nba-2022-EasternStandardTime.csv")
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
    if use_last_weeks_lineup:
        away_players = away_team.roster
        home_players = home_team.roster
    else:
        away_players = league.box_scores(week-use_last_weeks_lineup)[matchup].away_lineup
        home_players = league.box_scores(week-use_last_weeks_lineup)[matchup].home_lineup
    if use_last_weeks_lineup:
        df2 = pd.DataFrame(data=[[str(home_team).split("(")[1][:-1],0,0,str(away_team).split("(")[1][:-1],0,0]],columns=['Home Team','Home Score','Home Predicted Score','Away Team','Away Score','Away Predicted Score'])
    else:
        df2 = pd.DataFrame(data=[[str(home_team).split("(")[1][:-1],home_score,0,str(away_team).split("(")[1][:-1],away_score,0]],columns=['Home Team','Home Score','Home Predicted Score','Away Team','Away Score','Away Predicted Score'])
    for i in range(min(len(home_players),len(away_players))):
        if use_last_weeks_lineup:
            name_filter = X_test[X_test.index.get_level_values("Name")==str(home_players[i]).split(',')[0].split('(')[1][:-1]+'  ']
        else:
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
        if use_last_weeks_lineup:
            name_filter = X_test[X_test.index.get_level_values("Name")==str(away_players[i]).split(',')[0].split('(')[1][:-1]+'  ']
        else:
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
            if use_last_weeks_lineup:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1][:-1],'Home Score':str(0.0),'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1][:-1],'Away Score':str(0.0),'Away Predicted Score':round(predicted_away,2)},ignore_index=True)
            else:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(0.0),'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(0.0),'Away Predicted Score':round(predicted_away,2)},ignore_index=True)
        else:
            if use_last_weeks_lineup:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1][:-1],'Home Score':str(0.0),'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1][:-1],'Away Score':str(0.0),'Away Predicted Score':round(predicted_away,2)},ignore_index=True)
            else:
                df2 = df2.append({'Home Team':str(home_players[i]).split(',')[0].split('(')[1],'Home Score':str(home_players[i]).split(',')[1].split(':')[1][:-1],'Home Predicted Score':round(predicted_home,2),'Away Team':str(away_players[i]).split(',')[0].split('(')[1],'Away Score':str(away_players[i]).split(',')[1].split(':')[1][:-1],'Away Predicted Score':round(predicted_away,2)},ignore_index=True)

    df2['Home Predicted Score'][0] = df2['Home Predicted Score'][1:].sum().round(0)
    df2['Away Predicted Score'][0] = df2['Away Predicted Score'][1:].sum().round(0)

    df2 = df2.astype(str)
    
    data = X_test.reset_index()
    on_roster = pd.read_excel('data/players_from_rosters.xlsx')
    data['Name']=data['Name'].str[:-2]
    df4 = data[~data['Name'].isin(list(on_roster[0]))]
    df4['Games_next_week']=games_this_week[df4['Tm']].values
    df4 = df4.set_index(['Name','Week','Tm'])
    df4['Predicted_FP']=model_gp.predict(df4).round(0).values
    df4 = df4.reset_index()
    df4['Score'] = round(df4['Games']*df4['FPoints'],2)
    df4['Score'] = df4['Score'].shift(-1)
    df4 = df4[df4['Week']==week-2]
    df4 = df4[['Name','Games_next_week','Predicted_FP','Score']]
    df4 = df4.sort_values(by='Predicted_FP',ascending=False)
    df4 = df4.head(10)
    df3 = df4.astype(str)

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
    table2 = html.Div(
        [
            dash_table.DataTable(
                data=df3.to_dict("rows"),
                columns=[{"id": x, "name": x} for x in df3.columns],
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


    return [table],[table2]


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
