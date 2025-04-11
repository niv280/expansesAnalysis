import os, sys, glob, re, shutil
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import vizro
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import dash_loading_spinners as dls
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import json
import forex_python.converter
import subprocess
import Transactions

class App():
    def load_json(self):
        if os.path.isfile('./data/categories.json'):
            self.categories = json.load(open('./data/categories.json',"r"))
        else:
            self.categories = {'description' : {}}
        if os.path.isfile('./data/ignore_data.json'):
            self.ignore_data_list = json.load(open('./data/ignore_data.json',"r"))
        else:
            self.ignore_data_list = []
        self.currencyRates = forex_python.converter.CurrencyRates()
    
    def load_transactions(self):
        dataDir = "/".join(os.path.realpath(__file__).split('/')[:-1]) \
                   + '/../../data/'
        self.trans = Transactions.AllTransactions(dataDir)

    def __init__(self):
        # ============ transactions ===================
        dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
        self.app  = Dash(__name__,external_stylesheets=[dbc.themes.DARKLY, dbc.icons.FONT_AWESOME,dbc_css])
        self.load_json()
        self.load_transactions()
        tabs_list =  [dmc.TabsList([dmc.Tabs(k, value=str(i)) for i, k in enumerate(self.trans.trans.keys()) ])] + \
                     [dmc.TabsPanel(k, value=k) for i, k in enumerate(self.trans.trans.keys())]
    
        update_category = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Update Category")),
                dbc.ModalBody([
                        dbc.Label("body", id="body"),
                        dbc.Input(id="category_input"),
                        dbc.Button("Add",id="add_category")
                ])
            ],
            id = "update_category",
            is_open=False,
        )

        add_data = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Add data")),
                dbc.ModalBody([
                        dbc.Label("Description", id="add_data_description_label"),
                        dbc.Input(id="add_data_description"),
                        dbc.Label("Date", id="add_data_date_label"),
                        dbc.Input(id="add_data_date"),
                        dbc.Label("Amount", id="add_data_amount_label"),
                        dbc.Input(id="add_data_amount"),
                        dbc.Button("Add",id="apply_add_data"),
                ])
            ],
            id = "add_data",
            is_open=False,
        )

        ignore_data = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Ignore data")),
                dbc.ModalBody([
                        dbc.Label("ignore_data_body", id="ignore_data_body"),
                        dbc.Input(id="ignore_data_input"),
                        dcc.Dropdown(id='ignore_type', clearable=False,value="category", searchable=True, placeholder="Choose month..."),
                        dbc.Button("Ignore",id="apply_ignore_data")
                ])
            ],
            id = "ignore_data",
            is_open=False,
        )

        show_category = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Category")),
                dbc.ModalBody([
                        dash_table.DataTable(
                                id='category_table',
                        ),
                        html.H2(id='total_category', style={'fontSize': '12px'}),
                        html.H2(id='average_category', style={'fontSize': '12px'}),
                ])
            ],
            size="xl",
            id = "show_category",
            is_open=False,
        )

        color_mode_switch = html.Span(
        [
            dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
            dbc.Switch(id="color-mode-switch", value=False, className="d-inline-block ms-1", persistence=True),
            dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        ],
        style={"width": "20%", 'padding': 30, "textAlign": 'center', 'justifyContent': 'center'},
        )

        # dummy output needed by the clientside callback
        blank = html.Div(id="blank_output")
        rootLayout =  [
            blank,
            html.Div(id='refresh', style={'display': 'none'}),
            dbc.Row([
                html.Div([ 
                        html.P("Year:"),
                        dcc.Dropdown(id='year', clearable=False,value=[str(datetime.today().year)], searchable=True)
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center', 'display' : 'inline-block'}),
                html.Div([ 
                        html.P("Month:"),
                        dcc.Dropdown(id='month', clearable=False, value="All", searchable=True, placeholder="Choose month...")
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center'}),
                html.Div(children=[ 
                    daq.BooleanSwitch(on=True, label="Category", id='catogarized_switch'),
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center'}),
                html.Div(children=[ 
                    daq.BooleanSwitch(on=True, label="Ignore", id='ignore_switch'),
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center', 'display' : 'inline-block'}),
                html.Div([
                    html.Button('Fetch data', id='fetch_data', n_clicks=0),
                    html.Button('Add data', id='add_data_button', n_clicks=0),
                    html.Button('Ignore data', id='ignore_data_button', n_clicks=0),
                    dcc.Loading(
                        id="loading",
                        children=[html.Div([html.Div(id="loading-fetchData")])],
                        type="circle",
                    ),
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center'}),
                html.Div([ 
                    dash_table.DataTable(
                        id='total_sum',
                    ),
                ],
                className="dbc",
                style={"width" : "20%", 'padding' : 30, "textAlign" : 'center', 'justiftContent' : 'center'}),
                color_mode_switch,
            ]),
            dbc.Col([
                    dls.Hash(
                        dcc.Graph(id="graph", style={'width': '90000', 'height': '90000'}),
                        speed_multiplier=2,
                    ),
            ]),
            html.Div([
                dbc.Row([
                    update_category,
                    show_category,
                    add_data,
                    ignore_data,
                ])],
            className="dbc")
        ]
        self.app.layout = html.Div(id='main_layout', children=rootLayout)

        # trick to change the external stylesheet with callback
        self.app.clientside_callback(
            """
            function(themeToggle) {
                //  To use different themes,  change these links:
                const theme1 = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"
                const theme2 = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/minty/bootstrap.min.css"
                const stylesheet = document.querySelector('link[rel=stylesheet][href^="https://cdn.jsdelivr"]')        
                var themeLink = themeToggle ? theme1 : theme2;
                stylesheet.href = themeLink
            }
            """,
            Output("blank_output", "children"),
            Input("color-mode-switch", "value"),
        )
        @self.app.callback(
            Output('update_category','is_open',allow_duplicate=True),
            Input('add_category','n_clicks'),
            State('category_input','value'),
            State('body','children'),
            prevent_initial_call =True
        )
        def update_categories(n_clicks, input_value, description):
            self.categories['description'][description] = input_value
            json_data = json.dumps(self.categories, indent=4, sort_keys=True, ensure_ascii=False)
            with open('./data/categories.json', 'wb') as fp:
                fp.write(json_data.encode('utf-8'))
            return False
    
        @self.app.callback(
            Output('add_data','is_open',allow_duplicate=True),
            Input('add_data_button','n_clicks'),
            prevent_initial_call =True
        )
        def add_data_start(n_clicks):
            return True

        @self.app.callback(
            Output('add_data','is_open',allow_duplicate=True),
            Input('apply_add_data','n_clicks'),
            State('add_data_description','value'),
            State('add_data_date','value'),
            State('add_data_amount','value'),
            prevent_initial_call =True
        )
        def add_data(n_clicks, new_description, new_date, new_amount):
            new_data = { "identified" : "NA",
                         "date" : str(new_date),
                         "chargedAmount" : str(new_amount),
                         "originalCurrency" : "ILS",
                         "type" : "NA",
                         "description" : str(new_description),
                         "status" : "completed" }
            new_data_df = pd.DataFrame([new_data])
            # append new_data_df to existing csv
            if os.path.isfile("./data/added_data.csv"):
                existing_df = pd.read_csv("./data/added_data.csv")
                combined_df = pd.concat([existing_df, new_data_df], ignore_index=True)
                combined_df.to_csv("./data/added_data.csv", index=False)
            else:
                new_data_df.to_csv("./data/added_data.csv", index=False)

            # add new_data_df to current_df
            list(self.trans.trans.values())[0].df = pd.concat([list(self.trans.trans.values())[0].df, new_data_df], ignore_index=True)
            print(list(self.trans.trans.values())[0].df)
            return False 

        @self.app.callback(
                Output("month","options"),
                Output("year","options"),
                Input("year", "value"),
                Input("month", "value"))
        def get_date(year, month):
            months = list(self.trans.trans.values())[0].months + ["All"]
            years  = list(self.trans.trans.values())[0].years + ["All"]
            return months, years

        @self.app.callback(
            Output("graph", "figure"), 
            Output("total_sum", "data"), 
            Input("month", "value"),
            Input("year", "value"),
            Input("catogarized_switch", "on"),
            Input("ignore_switch", "on"),
            Input("update_category", "is_open"),
            Input("graph", "clickData"), 
            Input("color-mode-switch", "value")
        )
        def generate_chart(month, year, catogarized, ignore, is_open, clickData, dark_mode):
            df = list(self.trans.trans.values())[0].df
            if df.empty:
                fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
                return [fig, {}]
            if month == "All":
                month = ""
            if year == "All":
                year = ""
            df = df[df.date.str.contains(f'{year}-{month}',regex=True)]
            income_df = list(self.trans.trans.values())[0].income_df
            income_df = income_df[income_df.date.str.contains(f'{year}-{month}', regex=True)]
            values = 'chargedAmount'

            if catogarized:
                df = df.replace(self.categories)
                df.loc[~df['originalCurrency'].str.contains("ILS|₪"),'description'] = 'Vacation'
                income_df = income_df.replace(self.categories)
            if ignore:
                df = df[~df.description.isin(self.ignore_data_list)]
                income_df = income_df[~income_df.description.isin(self.ignore_data_list)]

            # Create subplots:
            if clickData:
                pull_list = [0.05 if clickData['points'][0]['label']==d else 0 for d in df.description.to_list() ]
            else:
                pull_list = [0 for d in df.description.to_list() ]

            if year == str(datetime.today().year):
                total_months = datetime.today().month
            else:
                total_months = 12

            if len(set(df['description'].to_list())) > 50:
                textinfo = "none"
            else:
                textinfo = "percent"

            fig = make_subplots(rows=2, cols=2, specs=[[{'type':'bar','colspan':2},None],[{'type':'domain'},{'type':'domain'}]],row_heights=[0.7, 0.3])

            if catogarized:
                # create new df with column of months from date column and different columns per description which the value is the chargedAmount
                df_pivot = df.assign(month=pd.to_datetime(df['date']).dt.month)
                df_pivot = df_pivot.groupby(['month','description']).agg({'chargedAmount': 'sum'}).reset_index()
                df_pivot = df_pivot.sort_values(by='chargedAmount', ascending=False)
            
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                         '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                         '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
                         '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5']
                # create list of unique description sorted by chargedAmount from df_pivot list
                description_list = list(set(df_pivot.description.to_list()))
                description_list.sort(key=lambda x: df_pivot[df_pivot['description']==x]['chargedAmount'].sum(), reverse=True)
                
                # Sort df_pivot by month and chargedAmount
                df_pivot = df_pivot.sort_values(['month', 'chargedAmount'], ascending=[True, False])
                
                for i,desc in enumerate(description_list):
                    if desc in self.categories['description'].values():
                        monthly_data = df_pivot[df_pivot['description']==desc].sort_values('month')
                        bar = go.Bar(name=desc, 
                                   x=monthly_data['month'], 
                                   y=monthly_data[values],
                                   marker_color=colors[i % len(colors)],
                                   text=desc,
                                   customdata=[desc]*len(monthly_data),
                                   hovertemplate='%{y:,.2f}')
                        fig.add_trace(bar,
                                      row=1, col=1)

            fig.update_layout(barmode='stack')
            fig.add_trace(go.Pie(labels=income_df.description.to_list(), values=income_df[values].to_list(), name="Income",pull=pull_list,hole=.4,hoverinfo="label+percent+value+name"),
                          row=2, col=1)
            fig.add_trace(go.Pie(labels=df['description'].to_list(), values=df[values].to_list(), name="Expanses",textinfo=textinfo, pull=pull_list,hole=.4,hoverinfo="label+percent+value+name"),
                          row=2, col=2)
            
            fig.update_layout(
                showlegend=False,
                title_text="Transactions",
                annotations=[dict(text='Income', x=0.18, y=0.5, font_size=20, showarrow=True),
                           dict(text='Expanse', x=0.82, y=0.5, font_size=20, showarrow=True)],
                height=1200,
                width=1200,
                paper_bgcolor='#222222' if dark_mode else 'white',  # DARKLY background color
                plot_bgcolor='#222222' if dark_mode else 'white',   # DARKLY background color
                font_color='#ffffff' if dark_mode else 'black',     # Text color
            )

            # Update axes for dark mode
            fig.update_xaxes(
                gridcolor='#444444' if dark_mode else '#e6e6e6',     # Grid lines color
                zerolinecolor='#444444' if dark_mode else '#e6e6e6', # Zero line color
                linecolor='#444444' if dark_mode else '#e6e6e6'      # Axis line color
            )
            
            fig.update_yaxes(
                gridcolor='#444444' if dark_mode else '#e6e6e6',     # Grid lines color
                zerolinecolor='#444444' if dark_mode else '#e6e6e6', # Zero line color
                linecolor='#444444' if dark_mode else '#e6e6e6'      # Axis line color
            )

            # remove Vacation from summary
            expanse_df = df[df['description']!="Vacation"] 
        
            sum_txt = { f"Total expanses": round(expanse_df[values].sum(),2),
                        f"Average expanses":round(expanse_df[values].sum()/(total_months),2),
                        f"Vacation":round(df[df['description']=="Vacation"][values].sum(),2),
                        f"Total income": round(income_df[values].sum(),2),
                        f"Average income": round(income_df[values].sum()/(total_months),2) }

            return [fig, pd.DataFrame(sum_txt.items(),columns=["Name","Value"]).to_dict('records')]
        
        @self.app.callback(
            Output("update_category","is_open"),
            Output("body","children"),
            Output("show_category","is_open"),
            Output("category_table","data"),
            Output("graph","clickData"),
            Output("total_category","children"),
            Output("average_category","children"),
            Input("graph","clickData"),
            State("catogarized_switch","on"),
            State("month", "value"),
            State("year", "value"),
            prevent_initial_call =True
        )
        def click(clickData, catogarized, month, year):
            if catogarized:
                if clickData and "points" in clickData.keys() and 'label' in clickData['points'][0].keys():
                    label = clickData['points'][0]['label']

                    if "custum_data" in clickData['points'][0]: 
                        custum_data = clickData['points'][0]['customdata']
                        if custum_data in self.categories['description'].values():
                            month = label
                            label = custum_data

                    if label in self.categories['description'].values() or label=="Vacation":
                        regex_month = "" if month == "All" else str(month).zfill(2)
                        month = 12 if month == "All" else month
                        df = list(self.trans.trans.values())[0].df
                        print(df.date.str.contains(f'{year}-{regex_month}'),regex_month)
                        df = df[df.date.str.contains(f'{year}-{regex_month}',regex=True)]
                        df['category'] = df['description'].replace(self.categories['description'])
                        df.loc[~df['originalCurrency'].str.contains("ILS|₪"),'category'] = 'Vacation'
                        df = df[df['category'] == label][['description', 'chargedAmount','category','date']]
                        return [False, label, True, df.to_dict('records'), clickData, f"Total:    {round(df['chargedAmount'].sum(),2)}", f"Average: {round(df['chargedAmount'].sum()/month,2)}" ]
                else:
                    label = "NA"
                return [True, label, False, {}, None, 0,0]

            return [False, False, False, {}, clickData, 0, 0]

        @self.app.callback(
            Output("year","value",allow_duplicate=True),
            Output("month","value",allow_duplicate=True),
            Output("loading-fetchData","children"),
            Input("fetch_data","n_clicks"),
            prevent_initial_call =True
        )
        def fetchData(n_clicks):
            config = json.load(open('./.config.json',"r"))

            # find the new start date
            dates = pd.to_datetime(self.trans.trans['Summary'].df['date'])
            startDate = f"{dates.max().year}-{dates.max().month}-{dates.max().day}"
            config['options']['startDate'] = startDate
            # backup data dir
            if os.path.exists('./data.bu'):
                shutil.rmtree('./data.bu')
            shutil.copytree('./data', './data.bu')
            print(f"-I- Extracting data from dates {dates.max().year}-{dates.max().month}-{dates.max().day}") 
            
            with open('./.config.tmp.json', 'w') as jf:
                json_data = json.dumps(config, indent=4)
                jf.write(json_data)

            p = subprocess.Popen(['node','./src/index.js','./.config.tmp.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()

            print(out.decode(), err.decode())
            #os.remove('./.config.tmp.json')
            self.load_transactions()
            print("===== END Fetch Data ==========")
            return datetime.today().year, datetime.today().month

        @self.app.callback(
            Output('ignore_data','is_open',allow_duplicate=True),
            Input("ignore_data_button","n_clicks"),
            prevent_initial_call =True
        )
        def ignore_data_start(n_clicks):
            return True    

        @self.app.callback(
            Output('ignore_data','is_open',allow_duplicate=True),
            Input('apply_ignore_data','n_clicks'),
            State('ignore_data_input','value'),
            State('body','children'),
            prevent_initial_call =True
        )
        def update_ignore_data(n_clicks, input_value, description):
            self.ignore_data_list = self.ignore_data_list + [input_value]
            json_data = json.dumps(self.ignore_data_list, indent=4, sort_keys=True, ensure_ascii=False)
            with open('./data/ignore_data.json', 'wb') as fp:
                fp.write(json_data.encode('utf-8'))
            print(f"-E- Ignoring from {input_value}")
            return False

# ====== create Dashboard ======================
app = App()
app.app.run_server(debug=True, dev_tools_hot_reload=False)
