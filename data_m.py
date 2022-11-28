import pandas as pd
import scipy.stats

def AssignValue(team, d, result):
    if team in d:
        if not isinstance(d[team], list):
            d[team] = [d[team]]
        d[team].append(result)
    else:
        d[team] = result
    return d

def findScores(league,scores,scores_against):
    for week in range(1,12):
        for matchup in league.scoreboard(week):
            team1 = str(matchup.home_team)[5:-1]
            team2 = str(matchup.away_team)[5:-1]
            score1 = matchup.home_final_score
            score2 = matchup.away_final_score
            scores = AssignValue(team1,scores,score1)
            scores = AssignValue(team2,scores,score2)
            scores_against = AssignValue(team1,scores_against,score2)
            scores_against = AssignValue(team2,scores_against,score1)
    return scores,scores_against

def createDataFrame(scores,scores_against):
    df = pd.DataFrame.from_dict(scores).T
    df['for'] = 1
    df3 = pd.DataFrame.from_dict(scores_against).T
    df3['for'] = 0
    df = df.append(df3).reset_index()
    table = pd.pivot_table(df,index=['index','for'])
    table2 = pd.DataFrame(table.stack())
    table2.index.names = ['teams','for','week']
    table2.columns = ['score']
    df_pts_for = table2.drop(0,level='for').reset_index(level='for', drop=True)
    df_pts_ag = table2.drop(1,level='for').reset_index(level='for', drop=True)
    df_pts_for['Mean_Opponent'] = (df_pts_for.groupby('week')['score'].transform('sum') - df_pts_for['score'])/(len(df_pts_for.groupby('teams')['score'])-1)
    df_pts_for['normalized score'] = df_pts_for['score'] - df_pts_for['Mean_Opponent']
    df_pts_ag['Mean_Opponent'] = (df_pts_ag.groupby('week')['score'].transform('sum') - df_pts_ag['score'])/(len(df_pts_ag.groupby('teams')['score'])-1)
    df_pts_ag['normalized score'] = df_pts_ag['score'] - df_pts_ag['Mean_Opponent']

    # removes incomplete weeks
    if 0 in df_pts_for.values:
        df_pts_for = df_pts_for.drop(0,level='week')
        df_pts_for = df_pts_for[(df_pts_for.T != 0).any()]
    if 0 in df_pts_ag.values:
        df_pts_ag = df_pts_ag.drop(0,level='week')
        df_pts_ag = df_pts_ag[(df_pts_ag.T != 0).any()]

    df_pts_for['3_week_rolling_mean'] = df_pts_for.groupby('teams')['normalized score'].rolling(3).mean().values
    df_pts_for['Margin'] = df_pts_for['score'] - df_pts_ag['score']
    df_pts_for['Won?'] = 0
    for i in df_pts_for.index.values:
        if df_pts_for['Margin'][i] >0:
            df_pts_for['Won?'][i] = 1
        else:
            df_pts_for['Won?'][i] = 0
    df_pts_for['Cumul_wins'] = df_pts_for.groupby('teams')['Won?'].cumsum()
    df_pts_ag = df_pts_ag.reset_index(level=[0,1])
    df_pts_for = df_pts_for.reset_index(level=[0,1])

    return df_pts_for,df_pts_ag, df

# def ReplaceTeamNames(df):
#     #region
#     my_dict = {'Ballpark Franks':'Team 1','Boban  Marjanovic ':'Team 2','Double Pandemic P':'Team 3',
#     'Frankpark Balls':'Team 4','FuxEm_Like ARabbott':'Team 5','Harrisburg Frank':'Team 6','King James  MVP 2021':'Team 7',
#     'Robin Lopez is bad':'Team 8','Buddy and Bam Hitting Traes':'Team 8',"Detroit Lonzo’s Balls":'Team 3',"Frankenstein's Monster (cock) ":'Team 1',
#     "Not Frank":'Team 7','St. Joan of Arc CYO Team':'Team 9','Team Bestbrook':'Team 10','Free Win':'Team 4'}
#     #endregion
#     df = df.replace(my_dict)
#     return df

def CreatePValues(df):
    ptsfor = df[df['for']==1].drop(columns=['for',0])
    ptsfor = ptsfor.set_index('index').T
    pdf = pd.DataFrame(columns=['team1','team2','pval'])
    tm1 = []
    tm2 = []
    pv = []
    for j in range(len(ptsfor.columns)):
        for i in range(len(ptsfor.columns)):
            if j < len(ptsfor.columns) and i<len(ptsfor.columns):
                team1 = ptsfor.columns[j]
                team2 = ptsfor.columns[i]
                stat, pval = scipy.stats.ttest_ind(ptsfor[team1],ptsfor[team2])
                if stat <0:
                    pval = 1-0.5*pval
                elif stat ==0:
                    pval=1
                else:
                    pval = 0.5*pval
                tm1.append(team1)
                tm2.append(team2)
                pv.append(pval)

    pdf = pd.DataFrame()
    pdf['team1'] = tm1
    pdf['team2'] = tm2
    pdf['pvalue'] = pv
    pdf = pd.pivot_table(pdf, values='pvalue',index='team1',columns='team2')
    return pdf