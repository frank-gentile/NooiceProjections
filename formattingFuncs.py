import plotly.graph_objs as go
import requests
import pandas as pd
import bs4 as bs
from scipy.stats import ttest_ind
from espn_api.basketball import League
import random

def formatLinks(player_names,year):
    links = []
    special = ['Anthony Davis','Jaren Jackson Jr.','Jaylen Brown','Harrison Barnes','Tobias Harris', 'Kevin Porter Jr.','Gary Trent Jr.','Cam Thomas','Jaxson Hayes','Markus Howard','Jared Butler','Miles Bridges','Bojan Bogdanovic','Kemba Walker','Patty Mills','Trey Murphy III','Keegan Murray']
    special4 =['Robert Williams III','Keldon Johnson','Jalen Smith']
    special5 = ['Jalen Green','Jabari Smith Jr.']
    special3 = ['Dennis Smith Jr.','Marcus Morris Sr.']
    

    if type(player_names)==str:
        first_name = player_names.split(" ")[0]
        last_name = player_names.split(" ")[1]
        first_letter = last_name[0].casefold()
        first_five = last_name[0:5].casefold()
        first_two = first_name[0:2].casefold()
        links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
        if player_names in special:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
        if player_names in special4:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'04/gamelog/'+str(year)
        if player_names == "D'Angelo Russell":
            links = 'https://www.basketball-reference.com/players/r/russeda01.html'
        if player_names in special3:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'03/gamelog/'+str(year)
        if player_names == "Clint Capela":
            links = 'https://www.basketball-reference.com/players/c/capelca01/gamelog/'+str(year)
        if player_names == 'RJ Barrett':
            links = 'https://www.basketball-reference.com/players/b/barrerj01/gamelog/'+str(year)
        if player_names in special5:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'05/gamelog/'+str(year)
        if player_names == 'O.G. Anunoby':
            links = 'https://www.basketball-reference.com/players/a/anunobyog01/gamelog/'+str(year)
    else:
        for player in player_names:
            first_name = player.split(" ")[0]
            last_name = player.split(" ")[1]
            first_letter = last_name[0].casefold()
            first_five = last_name[0:5].casefold()
            first_two = first_name[0:2].casefold()
            link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
            if player in special:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
            if player in special4:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'04/gamelog/'+str(year)
            if player == "D'Angelo Russell":
                link = 'https://www.basketball-reference.com/players/r/russeda01.html'
            if player in special3:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'03/gamelog/'+str(year)
            if player == "Clint Capela":
                link = 'https://www.basketball-reference.com/players/c/capelca01/gamelog/'+str(year)
            if player == 'RJ Barrett':
                link = 'https://www.basketball-reference.com/players/b/barrerj01/gamelog/'+str(year)
            if player in special5:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'05/gamelog/'+str(year)
            if player == 'O.G. Anunoby':
                link = 'https://www.basketball-reference.com/players/a/anunobyog01/gamelog/'+str(year)

            links.append(link)
    return(links)


def getPlayerData(link):
    # user_agent = random.choice(user_agent_list)
    # headers= {'User-Agent': user_agent, "Accept-Language": "en-US, en;q=0.5"}
    # proxy = random.choice(proxies)
    # response = get("your url", headers=headers, proxies=proxy)
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.content,'lxml')
    tables = soup.findAll('table')
    html = resp.text
    soup = bs.BeautifulSoup(html, 'lxml')
    links = soup.find_all('img')
    pic = links[1]['src']
    try:
        table = tables[-1]
    except:
        return 0, pic
    table_headers = []
    for tx in table.findAll('th'):
        table_headers.append(tx.text)
        if len(table_headers)==30:
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
                    # zeroes = [0]*29
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
    #player_data = player_data.drop(player_data.columns[3],axis=1)
    player_data_col_list = list(player_data.columns)
    player_data_col_list[4] = 'At'
    player_data_col_list[6] = 'W/L'
    player_data.columns = player_data_col_list
    return player_data, pic

def getTeams():
    league_id = 18927521

    league = League(league_id=league_id,year=2022)
    teams = []
    for team in league.teams:
        teams.append(team.team_name)
    teams.sort()
    return teams

#team_names = getTeams()

def getPlayersFromTeam(team_i):
    league_id = 18927521
    league = League(league_id=league_id,year=2022)
    player_list = []
    for i in range(len(league.teams[team_i].roster)):
        player_name = league.teams[team_i].roster[i].name
        player_list.append(player_name)
    return player_list

def getFantasyPoints(player_data):
    player_data['FPoints'] = 0
    if player_data['PTS'].astype('float').sum() ==0:
        player_data['FPoints']=0
        return player_data
    for index, row in player_data.iterrows():
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10) or (int(row['PTS'])>=10 and int(row['AST'])>=10) or (int(row['AST'])>=10 and int(row['TRB'])>=10) or \
        (int(row['PTS'])>=10 and int(row['BLK'])>=10) or (int(row['PTS'])>=10 and int(row['STL'])>=10):
            dd = 1
        else: 
            dd = 0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10):
            td=1
        else:
            td=0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10) and (int(row['BLK'])>=10 or int(row['STL'])>=10):
            qd = 1
        else: 
            qd=0
        player_data.loc[index,'FPoints'] = int(row['FG'])-int(row['FGA'])+int(row['FT'])-int(row['FTA'])+int(row['3P'])+int(row['TRB'])+int(row['AST'])+int(row['STL'])+int(row['BLK']) \
            -int(row['TOV'])+int(row['PTS'])+5*dd+10*td+1000*qd
    return player_data