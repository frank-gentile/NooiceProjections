#%%
import pandas as pd
from formattingFuncs import getFantasyPoints
import statsmodels.api as sm
import pickle
from sklearn.cluster import KMeans


year = 2022
def simplify(text):
	import unicodedata
	try:
		text = unicode(text, 'utf-8')
	except NameError:
		pass
	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
	return str(text)


def createXy(y_df,total_player_df_summed,big_team_df):
    for i in range(len(y_df['Name'])):
        y_df['Name'][i] = simplify(y_df['Name'][i])
    # for j in range(len(total_player_df_summed['Name'])):
    #     total_player_df_summed['Name'][j] = simplify(total_player_df_summed['Name'][j])

    total_player_df_summed['Name'] = total_player_df_summed['Name'].replace('Robert Williams  ','Robert Williams III  ')


    y_df = y_df.set_index(['G','Date','W/L','Opp','Age','At','Name'])
    total_player_df_summed = total_player_df_summed.set_index(['G','Date','Age','Opp','W/L','At','Name'])

    big_team_df = big_team_df.set_index(['G','Date','W/L','Team'])
    big_team_df.index = big_team_df.index.rename({'Team':'Opp'})

    total_player_df_summed = total_player_df_summed.merge(big_team_df,on=['Date','Opp'],how='left')
    total_player_df_summed = total_player_df_summed.astype(float)



    total_player_df_summed = total_player_df_summed.reset_index()
    total_player_df_summed['Name'] = pd.Series(y_df.reset_index().loc[:,'Name'])
    total_player_df_summed = total_player_df_summed.set_index(['Date','Opp','Name'])
    total_player_df_summed = total_player_df_summed.dropna()
    testy = y_df.droplevel(['G','Age','W/L','At'])
    y_df = testy[testy.index.isin(total_player_df_summed.index)]

    y_df = y_df.drop_duplicates()
    y_df = getFantasyPoints(y_df)
    y_fp = y_df['FPoints']
    y_pts = y_df['PTS']
    y_reb = y_df['TRB']
    y_ast = y_df['AST']
    X = total_player_df_summed.astype(float)
    X = X.drop_duplicates()
    X['weekday'] = pd.to_datetime(X.index.get_level_values('Date')).weekday
    X['week'] = pd.to_datetime(X.index.get_level_values('Date')).week
    X['month'] = pd.to_datetime(X.index.get_level_values('Date')).month
    X['day'] = pd.to_datetime(X.index.get_level_values('Date')).day
    X['month'] = X['month'] - 9
    X.loc[X['month']<0,'month']=X['month']+12
    X['week'] = X['week'] - 41
    X.loc[X['week']<0,'week']=X['week']+53

    return X, y_fp, y_pts, y_reb, y_ast 

y_df = pd.read_excel('data/y_df2021.xlsx')

total_player_df_summed = pd.read_excel('data/total_player_df2021.xlsx')

big_team_df = pd.read_excel('data/big_team_df2021.xlsx')

#%%
X, y, y_pts, y_reb, y_ast = createXy(y_df,total_player_df_summed,big_team_df)

optimal_clusters = 5
kmeans = KMeans(n_clusters=optimal_clusters,init='k-means++',random_state=0).fit(X)
labels = kmeans.fit_predict(X)
#assign labels to data points
X['Cluster'] = labels
X = pd.get_dummies(X['Cluster']).join(X).drop(['Cluster'],axis=1)
X = X[X.index.isin(y.index)]



#%%
model_fp = sm.OLS(y,X).fit()
model_pts = sm.OLS(y_pts,X).fit()
model_reb = sm.OLS(y_reb,X).fit()
model_ast = sm.OLS(y_ast,X).fit()
pickle.dump(model_fp, open('models/OLS_model_fp.sav', 'wb'))
pickle.dump(model_pts, open('models/OLS_model_pts.sav', 'wb'))
pickle.dump(model_reb, open('models/OLS_model_reb.sav', 'wb'))
pickle.dump(model_ast, open('models/OLS_model_ast.sav', 'wb'))

y_df_22 = pd.read_excel('data/y_df'+str(year)+'.xlsx')

total_player_df_summed_22 = pd.read_excel('data/total_player_df'+str(year)+'.xlsx')

big_team_df_22 = pd.read_excel('data/big_team_df'+str(year)+'.xlsx')

X_test, y_test, y_pts_test, y_reb_test, y_ast_test  = createXy(y_df_22,total_player_df_summed_22,big_team_df_22)

X_test.to_csv('X_test.csv')

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

model_gp_fp, X_test_fp, X_fp = dropColumns(model_fp, X, X_test, y,1)
model_gp_pts, X_test_pts, X_pts = dropColumns(model_pts, X, X_test, y_pts,1)
model_gp_reb, X_test_reb, X_reb = dropColumns(model_reb, X, X_test, y_reb,1)
model_gp_ast, X_test_ast, X_ast = dropColumns(model_ast, X, X_test, y_ast,1)

#%%
pickle.dump(model_gp_fp, open('models/finalized_model_fp.sav', 'wb'))
pickle.dump(model_gp_pts, open('models/finalized_model_pts.sav', 'wb'))
pickle.dump(model_gp_reb, open('models/finalized_model_reb.sav', 'wb'))
pickle.dump(model_gp_ast, open('models/finalized_model_ast.sav', 'wb'))

def saveXtest(X_test,label):
    X_test.to_csv('data/'+label+'.csv')

saveXtest(X_test_fp,'fp')
saveXtest(X_test_pts,'pts')
saveXtest(X_test_reb,'reb')
saveXtest(X_test_ast,'ast')

