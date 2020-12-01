import dash
import dash_player
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_auth

import datetime
import sys
import os
import glob
import base64

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# app requires "pip install psycopg2" as well

# format logos and pics
image_filename1 = 'assets/hh_logo.png'
encoded_image1 = base64.b64encode(open(image_filename1, 'rb').read())
TOWERS_LOGO = 'data:image/png;base64,{}'.format(encoded_image1.decode())

nav_item_1 = dbc.NavItem(dbc.NavLink("Scouting", href="/"))
nav_item_2 = dbc.NavItem(dbc.NavLink("Database", href="/apps/database"))


external_stylesheets = [dbc.themes.BOOTSTRAP]

server = Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)
app.server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


VALID_USERNAME_PASSWORD_PAIRS = {'Partizan': 'good2great'}

# Authentication
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)



# for your home PostgreSQL test table
# app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:Stanford@localhost/videoBase"

# for your live Heroku PostgreSQL database
app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgres://aqneikqjreopov:85d086eef04810140fedd88750eac607649e66f893e54b476e72cfe2f81ec3e1@ec2-54-228-250-82.eu-west-1.compute.amazonaws.com:5432/daeicqg112rv3p"

db = SQLAlchemy(app.server)

df = pd.read_sql_table('records', con=db.engine)
df['id'] = df['Id']
df.set_index('id', inplace=True, drop=False)

# class Product(db.Model):
#     __tablename__ = 'records'

#     Phone = db.Column(db.String(40), nullable=False, primary_key=True)
#     Version = db.Column(db.String(40), nullable=False)
#     Price = db.Column(db.Integer, nullable=False)
#     Sales = db.Column(db.Integer, nullable=False)

#     def __init__(self, phone, version, price, sales):
#         self.Phone = phone
#         self.Version = version
#         self.Price = price
#         self.Sales = sales


focus = ['Competition', 'Concepts', 'Skills', 'Decision', 'Sets']
audience = ['Individual', 'Group', 'Combo']
fundamental = ['Passing', 'Shooting', 'Dribling', 'Finishing']
defenseLevel = ['No Defense', 'Guide Defense', 'Contact Defense']
emphasis = ['Create Advantage', 'Finishing Advantage', 'Using Advantage']
offense = ['BOB', 'SOB', 'Drive&Kick-Dish', 'Close Out', 'Fastbreak', 'Transition', 'Top PnR', 'Side PnR', 'Step Up PnR', 'Coming Off Screen', 'Post Up', 'Numbers', 'Zone Offense', 'Press Break']
defense = ['Close Out', 'Rebound', 'Transition', 'Coming Off Screen', 'Post Up', 'Press Defense', 'Zone Defense', 'Rebounding']
position = ['Guards', 'Bigs', 'Combo', 'Team']



# ------------------------------------------------------------------------------------------------

app.layout = html.Div([


    dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=TOWERS_LOGO, height="50px")),
                            dbc.Col(dbc.NavbarBrand("Drills Library", className="ml-2")),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="/",
                ),
            ]
        ),
        color="black",
        dark=True,
        className="mb-5",
    ),

    html.Br(),

    # html.Div([
    #     dcc.Input(
    #         id='adding-rows-name',
    #         placeholder='Enter a column name...',
    #         value='',
    #         style={'padding': 10}
    #     ),
    #     html.Button('Add Column', id='adding-columns-button', n_clicks=0)
    # ], style={'height': 50}),

    # html.Button('Add Row', id='editing-rows-button', n_clicks=0),
    html.Button('Save to Database', id='save_to_postgres', n_clicks=0),

    dcc.Interval(id='interval_pg', interval=86400000*7, n_intervals=0),  # activated once/week or when page refreshed

    html.Br(),
    html.Br(),

    html.Div(id='postgres_datatable'),



    # Create notification when saving to excel/database
    html.Div(id='placeholder', children=[]),
    dcc.Store(id="store", data=0),
    dcc.Interval(id='interval', interval=1000),

    html.Br(),
    html.Br(),
    html.Br(),


    html.Div(id='datatable-to-video'),

    # dash_player.DashPlayer(
    #     id = 'video-replay',
    #     url='https://drillslibrary-store.s3.eu-central-1.amazonaws.com/best.mp4',

    #     #1on1_on_Ball_Pinciples.mp4',
    #     #url='http://s3.amazonaws.com/drillslibrary-store/1on1_on_Ball_Pinciples.mp4',
    #     # url=str("/" + df.at[active_row_id, 'Link']),
    #     # url=str('http://s3.amazonaws.com/bucketname/' + df.at[active_row_id, 'Link']),
    #     controls=True,
    #     width='100%'
    # ),


])


# --------------------------------------------------------------------------


# return datatable
@app.callback(Output('postgres_datatable', 'children'),
              [Input('interval_pg', 'n_intervals')])
def populate_datatable(n_intervals):
    df = pd.read_sql_table('records', con=db.engine)
    return [
        dash_table.DataTable(
            id='our-table',
            columns=[
            {
                'name': str(x),
                'id': str(x),
                'deletable': False,
                'presentation': 'dropdown',
            } if x in ['Focus', 'Audience', 'Fundamental', 'DefenseLevel', 'Emphasis', 'Offense', 'Defense', 'Position']
            else {
                'name': str(x),
                'id': str(x),
                'deletable': False,
            }
            for x in df.columns],
            dropdown={
                'Focus': {
                    'options': [
                        {'label': i, 'value': i}
                        for i in ['Competition', 'Concepts', 'Skills', 'Decision', 'Sets']
                    ]
                },
                'Audience': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in audience
                    ]
                },
                'Fundamental': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in fundamental
                    ]
                },
                'DefenseLevel': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in defenseLevel
                    ]
                },
                'Emphasis': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in emphasis
                    ]
                },
                'Offense': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in offense
                    ]
                },
                'Defense': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in defense
                    ]
                },
                'Position': {
                     'options': [
                        {'label': i, 'value': i}
                        for i in position
                    ]
                },
            },
            data=df.to_dict('records'),
            editable=True,
            row_deletable=True,
            filter_action="native",
            sort_action="native",  # give user capability to sort columns
            sort_mode="multi",  # sort across 'multi' or 'single' columns
            selected_rows=[],
            page_action='native',
            page_current= 0,
            page_size= 10,
            # page_action='none',  # render all of the data at once. No paging.
            style_table={'height': '420px', 'overflowY': 'auto'},
            #style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
            style_cell_conditional=[
                {
                    'if': {'column_id': c},
                    'textAlign': 'right'
                } for c in ['Price', 'Sales']
            ] + [
               {
                    'if': {'column_id': 'id'},
                    'display': 'None',
               }
            ],
            style_header_conditional=[
                {'if': {'column_id': 'id',},
                    'display': 'None',}
            ],

        ),
    ]





# populate datatable-to-video on click on row
@app.callback(
    Output('datatable-to-video', 'children'),
    [Input('our-table', 'derived_virtual_row_ids'),
     Input('our-table', 'selected_row_ids'),
     Input('our-table', 'active_cell')])
def update_video(row_ids, selected_row_ids, active_cell):
    selected_id_set = set(selected_row_ids or [])
    if row_ids is None:
        dff = df
        # pandas Series works enough like a list for this to be OK
        row_ids = df['id']
    else:
        dff = df.loc[row_ids]

    active_row_id = active_cell['row_id'] if active_cell else None

    print("#-#-#-#-#-#-#-#-#-#-#-#-")
    print(active_row_id)
    print("#-#-#-#-#-#-#-#-#-#-#-#-")


    colors = ['#FF69B4' if id == active_row_id
              else '#7FDBFF' if id in selected_id_set
              else '#0074D9'
              for id in row_ids]

    if active_row_id:
        return [
            dbc.Row(
                dbc.Col(
                    html.Div(
                        dash_player.DashPlayer(
                            id = 'video-replay',
                            #url='https://drillslibrary-store.s3.eu-central-1.amazonaws.com/5on5_Zipper_into_Transition.mp4',
                            url=str("https://drillslibrary-store.s3.eu-central-1.amazonaws.com/" + df.at[active_row_id, 'Name']),
                            controls=True,
                            width='100%'
                        ),
                    ),
                width={"size": 10, "offset": 1},
                ),
            ),
        ]
    else:
        pass



# add column
@app.callback(
    Output('our-table', 'columns'),
    [Input('adding-columns-button', 'n_clicks')],
    [State('adding-rows-name', 'value'),
     State('our-table', 'columns')],
    prevent_initial_call=True)
def add_columns(n_clicks, value, existing_columns):
    if n_clicks > 0:
        existing_columns.append({
            'name': value, 'id': value,
            'renamable': True, 'deletable': True
        })
    return existing_columns


# add row
@app.callback(
    Output('our-table', 'data'),
    [Input('editing-rows-button', 'n_clicks')],
    [State('our-table', 'data'),
     State('our-table', 'columns')],
    prevent_initial_call=True)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows


# saved to database msg
@app.callback(
    [Output('placeholder', 'children'),
     Output("store", "data")],
    [Input('save_to_postgres', 'n_clicks'),
     Input("interval", "n_intervals")],
    [State('our-table', 'data'),
     State('store', 'data')],
    prevent_initial_call=True)
def df_to_csv(n_clicks, n_intervals, dataset, s):
    output = html.Plaintext("The data has been saved to your PostgreSQL database.",
                            style={'color': 'green', 'font-weight': 'bold', 'font-size': 'large'})
    no_output = html.Plaintext("", style={'margin': "0px"})

    input_triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if input_triggered == "save_to_postgres":
        s = 6
        pg = pd.DataFrame(dataset)
        pg.to_sql("records", con=db.engine, if_exists='replace', index=False)
        return output, s
    elif input_triggered == 'interval' and s > 0:
        s = s - 1
        if s > 0:
            return output, s
        else:
            return no_output, s
    elif s == 0:
        return no_output, s




if __name__ == '__main__':
    app.run_server(debug=True)
