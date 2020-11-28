import dash
import dash_player
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

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

# for your home PostgreSQL test table
# app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:Stanford@localhost/videoBase"

# for your live Heroku PostgreSQL database
app.server.config["SQLALCHEMY_DATABASE_URI"] = "postgres://aqneikqjreopov:85d086eef04810140fedd88750eac607649e66f893e54b476e72cfe2f81ec3e1@ec2-54-228-250-82.eu-west-1.compute.amazonaws.com:5432/daeicqg112rv3p"

db = SQLAlchemy(app.server)


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
                # dbc.NavbarToggler(id="navbar-toggler2"),
                # dbc.Collapse(
                #     dbc.Nav(
                #         [nav_item_1, nav_item_2], className="ml-auto", navbar=True
                #     ),
                #     id="navbar-collapse2",
                #     navbar=True,
                # ),
            ]
        ),
        color="black",
        dark=True,
        className="mb-5",
    ),


    # html.Div([
    #     dcc.Input(
    #         id='adding-rows-name',
    #         placeholder='Enter a column name...',
    #         value='',
    #         style={'padding': 10}
    #     ),
    #     html.Button('Add Column', id='adding-columns-button', n_clicks=0)
    # ], style={'height': 50}),

    dcc.Interval(id='interval_pg', interval=86400000*7, n_intervals=0),  # activated once/week or when page refreshed
    html.Div(id='postgres_datatable'),

    html.Button('Add Row', id='editing-rows-button', n_clicks=0),
    html.Button('Save to Database', id='save_to_postgres', n_clicks=0),

    # Create notification when saving to excel
    html.Div(id='placeholder', children=[]),
    dcc.Store(id="store", data=0),
    dcc.Interval(id='interval', interval=1000),

    html.Div(id='datatable-to-video'),

    dash_player.DashPlayer(
        id = 'video-replay',
        url='https://drillslibrary-store.s3.eu-central-1.amazonaws.com/Drill.mp4',

        #1on1_on_Ball_Pinciples.mp4',
        #url='http://s3.amazonaws.com/drillslibrary-store/1on1_on_Ball_Pinciples.mp4',
        # url=str("/" + df.at[active_row_id, 'Link']),
        # url=str('http://s3.amazonaws.com/bucketname/' + df.at[active_row_id, 'Link']),
        controls=True,
        width='100%'
    ),


])


# --------------------------------------------------------------------------


@app.callback(Output('postgres_datatable', 'children'),
              [Input('interval_pg', 'n_intervals')])
def populate_datatable(n_intervals):
    df = pd.read_sql_table('records', con=db.engine)
    return [
        dash_table.DataTable(
            id='our-table',
            columns=[{
                         'name': str(x),
                         'id': str(x),
                         # 'deletable': False,}
                #      } if x == 'Sales' or x == 'Phone'
                #      else {
                # 'name': str(x),
                # 'id': str(x),
                # 'deletable': True,
            }
                     for x in df.columns],
            data=df.to_dict('records'),
            editable=True,
            row_deletable=True,
            filter_action="native",
            sort_action="native",  # give user capability to sort columns
            sort_mode="single",  # sort across 'multi' or 'single' columns
            page_action='native',
            page_current= 0,
            page_size= 10,
            # page_action='none',  # render all of the data at once. No paging.
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
            style_cell_conditional=[
                {
                    'if': {'column_id': c},
                    'textAlign': 'right'
                } for c in ['Price', 'Sales']
            ]

        ),
    ]


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


# @app.callback(
#     Output('my_graph', 'figure'),
#     [Input('our-table', 'data')],
#     prevent_initial_call=True)
# def display_graph(data):
#     # df_fig = pd.DataFrame(data)
#     # fig = px.bar(df_fig, x='Phone', y='Sales')

#     pg_filtered = db.session.query(Product.Phone, Product.Sales)
#     phone_c = [x.Phone for x in pg_filtered]
#     sales_c = [x.Sales for x in pg_filtered]
#     fig = go.Figure([go.Bar(x=phone_c, y=sales_c)])

#     return fig


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



@app.callback(
    Output('datatable-to-video', 'children'),
    [Input('datatable-row-ids', 'derived_virtual_row_ids'),
     Input('datatable-row-ids', 'selected_row_ids'),
     Input('datatable-row-ids', 'active_cell')])
def update_video(row_ids, selected_row_ids, active_cell):
    selected_id_set = set(selected_row_ids or [])
    # if row_ids is None:
    #     dff = df
    #     # pandas Series works enough like a list for this to be OK
    #     row_ids = df['id']
    # else:
    #     dff = df.loc[row_ids]

    active_row_id = active_cell['row_id'] if active_cell else None

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
                            url='http://s3.amazonaws.com/drillslibrary-store/1on1_on_Ball_Pinciples.mp4',
                            # url=str("/" + df.at[active_row_id, 'Link']),
                            # url=str('http://s3.amazonaws.com/bucketname/' + df.at[active_row_id, 'Link']),
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





if __name__ == '__main__':
    app.run_server(debug=True)
