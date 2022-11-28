import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pandas as pd

def getLuckSkillPlot(df,df_against):
    fig = go.Figure()
    team_plot_names = []
    buttons=[]
    color_dict = {}
    color_list = px.colors.qualitative.Plotly
    team_df = pd.DataFrame(df['teams'].unique())
    for team in df['teams'].unique():
        color_dict[team] = color_list[team_df[team_df[0]==team].index[0]]
    for team in df['teams'].unique():
        ptsf = df[df['teams']==team]
        ptsa = df_against[df_against['teams']==team]
        ptsf['normalized score against'] = ptsa['normalized score']
        fig.add_trace(go.Scatter(x=ptsf['normalized score'],y=ptsa['normalized score'],
            mode='markers',visible=(team=="Ballpark Franks"),marker=dict(size=10,color=color_dict[team])))
        team_plot_names.extend([team])

    for team in df['teams'].unique():
        buttons.append(dict(method='update',
                            label=team,
                            args = [{'visible': [team==r for r in team_plot_names]}]))
        fig.add_trace(go.Scatter(
        x=[290, 200, -290,-200],
        y=[200, 300, -200,-300],
        text=["Good and won",
            "Unlucky loss",
            "Bad and lost",
            "Lucky win"],
        mode="text")) 
    
    fig.update_layout(showlegend=False, 
    updatemenus=[{"buttons": buttons, "direction": "down", "showactive": True, "x": 0.5, "y": 1.15}],
    xaxis=dict(title="Points for (normalized)"),
        yaxis=dict(title="Points against (normalized)"))
    fig.add_vline(x=0, line_width=3)
    fig.add_hline(y=0,line_width=3)
    fig.update_xaxes(range=[-400, 400])
    fig.update_yaxes(range=[-400, 400])
    fig.add_shape(type="line",
    x0=-400, y0=-400, x1=400,y1=400,
    line=dict(dash="dot",width=3))
    #fig.write_image("/Users/frankgentile/Documents/NBA/Nooice-Analytics/figs/luck.png",width=600, height=400)
    return fig

def getViolinPlots(df):
    fig = px.violin(df,x='teams',y='normalized score',color='teams')
    fig.update_layout(showlegend=False,xaxis=dict(title='Teams'),yaxis=dict(title="Points for (normalized)"))
    #fig.write_image("/Users/frankgentile/Documents/NBA/Nooice-Analytics/figs/violin.png",width=600, height=400)
    return fig


def PlotlyHeatmap(df):
    return px.imshow(df)