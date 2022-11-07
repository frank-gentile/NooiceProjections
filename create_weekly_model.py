#%%
import pandas as pd
from formattingFuncs import getFantasyPoints
import statsmodels.api as sm
import pickle
from sklearn.cluster import KMeans
from datetime import datetime, date, timedelta
from formattingFuncs import getPlayerData, getTeams, formatLinks,getPlayersFromTeam, getFantasyPoints
from retrieveData import getPlayerDataAdv
import numpy as np

year = 2023
week = 1
#start_date = datetime(2021,10,18)
start_date = datetime(2022,10,17)

run_new_player_data = 0
get_current_data =1


def simplify(text):
	import unicodedata
	try:
		text = unicode(text, 'utf-8')
	except NameError:
		pass
	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
	return str(text)


def createXy(player_data_joined):
    #player_data_joined = player_data_joined.reset_index()
    for i in range(len(player_data_joined["Name"])):
        player_data_joined['Name'][i] = simplify(player_data_joined["Name"][i])



    player_data_joined = player_data_joined.set_index(['G','Date','W/L','Opp','Age','At','Name','Tm'])
    player_data_joined = player_data_joined.astype(float)


    player_data_joined = getFantasyPoints(player_data_joined)
    y_fp = player_data_joined['FPoints']
    X = player_data_joined.astype(float)
    X = X.drop_duplicates()
    grouped_y = pd.DataFrame()
    grouped_x = pd.DataFrame()
    for week in range(52):
        start_date_week = start_date + timedelta(7*week)
        end_date_week = start_date_week + timedelta(7)
        y_df_local = y_fp[y_fp.index.get_level_values("Date") < str(end_date_week)[:10]]
        y_df_local = y_df_local[y_df_local.index.get_level_values("Date") >= str(start_date_week)[:10]]
        X_local = X[X.index.get_level_values("Date")<str(end_date_week)[:10]]
        X_local = X_local[X_local.index.get_level_values("Date")>=str(start_date_week)[:10]]

        games = y_df_local.groupby(["Name","Tm"]).count()
        games = games.rename('Games')

        weekly_x = X_local.groupby(["Name","Tm"]).sum()
        weekly_x = weekly_x/games[:,None]
        weekly_x = pd.concat([weekly_x,games,pd.Series([week]*len(games),name='Week',index=games.index)],axis=1)
        weekly_fp = y_df_local.groupby(["Name","Tm"]).sum()
        weekly_fp = pd.concat([weekly_fp,games,pd.Series([week]*len(games),name='Week',index=games.index)],axis=1)

        grouped_y = pd.concat([grouped_y,weekly_fp])
        grouped_x = pd.concat([grouped_x,weekly_x])

#stopped here- need to add lags to x
    return grouped_x, grouped_y

#y_df = pd.read_excel('data/y_df2021.xlsx')
#total_player_df_summed = pd.read_excel('data/total_player_df2021.xlsx')


#get correct player data
if run_new_player_data: 
    playerlist = pd.read_excel('data/NBA_players23.xlsx')['Player']
    links_list = formatLinks(playerlist,year)
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
        total_player_df_summed = pd.concat([total_player_df_summed,player_data_joined])
    total_player_df_summed.to_csv('data/tot_players'+str(year)+'.csv')
    total_player_df_summed = total_player_df_summed.reset_index()
else:
    total_player_df_summed = pd.read_csv('data/tot_players'+str(year)+'.csv')
    total_player_df_summed = total_player_df_summed.drop_duplicates()

    total_player_df_summed = total_player_df_summed.reset_index()

    total_player_df_summed = total_player_df_summed.drop(['index'],axis=1)


#%%
X, y = createXy(total_player_df_summed)
X_df = pd.DataFrame()


if not get_current_data:
#this is where the X shifts
    for i in range(len(total_player_df_summed['Name'].unique())):
        name = total_player_df_summed['Name'].unique()[i]
        X_local = X[X.index.get_level_values("Name") ==name]
        X_local = X_local.reset_index().set_index("Week").shift(1).dropna()
        X_local = X_local.reset_index()
        X_df = pd.concat([X_df,X_local])
else:
    X_df = X.copy()
    X_df = X_df.reset_index()

#X_df['Week'] = X_df['Week']
X_df = X_df.set_index(["Name","Week","Tm"])
y = y.reset_index()
if not get_current_data:
    y = y[y['Week']!=0]
#y['Week']=y['Week']
y_df = pd.DataFrame(y.set_index(["Name","Week","Tm"])).sort_index(level="Name")
X_df = X_df.sort_index(level="Name")
X_df['Games_next_week'] = y_df['Games']
y_df = y_df.drop(['Games'],axis=1)





optimal_clusters = 5
kmeans = KMeans(n_clusters=optimal_clusters,init='k-means++',random_state=0).fit(X_df)
labels = kmeans.fit_predict(X_df)
#assign labels to data points
X_df['Cluster'] = labels
X_df = pd.get_dummies(X_df['Cluster']).join(X_df).drop(['Cluster'],axis=1)
X_df = X_df[X_df.index.isin(y_df.index)]
y_df = y_df[y_df.index.isin(X_df.index)]


X_df.to_csv('data/X_df.csv')
y_df.to_csv('data/y_df.csv')

if not get_current_data:
    model = sm.GLM(y_df,X_df,family=sm.families.Poisson()).fit()
    pickle.dump(model, open('models/OLS_weekly_model_fp.sav', 'wb'))

    model_gp = pickle.load(open('models/OLS_weekly_model_fp.sav', 'rb'))

    y_hat = model_gp.predict(X_df)

    sq_mse = np.sqrt(np.mean((y_df['FPoints'] - y_hat)**2))
    print(sq_mse)

#%%

# y_df_22 = pd.read_excel('data/y_df'+str(year)+'.xlsx')

# total_player_df_summed_22 = pd.read_excel('data/total_player_df'+str(year)+'.xlsx')

#X_test, y_test = createXy(y_df_22,total_player_df_summed_22)

#X_test.to_csv('X_test_weekly.csv')

#%%
def dropColumns(model,X,X_test,y,add_clusters):
    for col in model.pvalues.index:
        if model.pvalues[col]>0.15:
            X = X.drop([col],axis=1)
            try:
                X_test = X_test.drop([col],axis=1)
            except:
                pass

    if add_clusters:
        optimal_clusters = 5
        kmeans = KMeans(n_clusters=optimal_clusters,init='k-means++',random_state=0).fit(X_test)
        labels = kmeans.fit_predict(X_test)
        #assign labels to data points
        X_test['Cluster'] = labels
        X_test = pd.get_dummies(X_test['Cluster']).join(X_test).drop(['Cluster'],axis=1)


    y = y[y>0]
    X = X[X.index.isin(y.index)]
    model_gp = sm.GLM(y, X, family=sm.families.Poisson()).fit()
    return model_gp, X_test, X

#model_gp_fp, X_test_fp, X_fp = dropColumns(model_fp, X, X_test, y,1)

#%%
#pickle.dump(model_gp_fp, open('models/finalized_model_fp.sav', 'wb'))

#def saveXtest(X_test,label):
    # X_test.to_csv('data/'+label+'.csv')

#saveXtest(X_test_fp,'fp_weekly')

