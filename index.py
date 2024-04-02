import dash
from dash import html
from dash.dependencies import Input, Output
from dash import dcc
from flask import Flask
import generate_graph
from help_functions import *
from dash import dash_table as dt
import traceback
import threading
import os
from waitress import serve


server = Flask(__name__)
server.secret_key = "test"
config = open_json("config.json")

app = dash.Dash(__name__, server=server)
app.title = "Market seasonality - trading data"
logs_directory = "logs"

months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
text_center = {"text-align": "center"}
table_center = {"marginLeft": "auto", "marginRight": "auto"}
dropdown_center = {
    "display": "flex",
    "align-items": "center",
    "justify-content": "center",
}


class Webpage:
    def __init__(self):
        self.make_page()

    def wait_to_start(self):
        while True:
            if safe == 1:
                print(f"{get_time_in_sk()} starting server...")
                break
            time.sleep(1.5)

    def start_server(self):
        self.wait_to_start()
        if config["is_test"]:
            app.run_server(debug=True, use_reloader=False)
        else:
            # THIS WILL MAKE SITE GO LIVE
            serve(
                app.server,
                host=config["ip"],
                port=config["port"],
                url_scheme="https",
            )

    def make_page(self):

        app.layout = html.Div(
            [
                # TITLE + TEXT
                html.H1("SPX seasonality", style=text_center),
                html.P(
                    [
                        "This website measures SPX performance / seasonality over the last selected years showing historical"
                        " market sentiment.",
                        html.Br(),
                        "This site is updated daily and always has the newest information. The point of this project is to "
                        "make a better daily trading decisions based on the past data.",
                        html.Br(),
                        "The site tells you the average % monthly gain and daily gain, so you can estimate how the market will behave at a given day."
                        "It has data going all the way tot he past 50 years.",
                        html.Br(),
                        "The first section contains this month/day data and second section has all the historical data.",
                    ],
                    style=text_center,
                ),
                html.Br(),
                # FIRST GRAPH MONTHLY
                html.H2("This month seasonality", style=text_center),
                html.P(
                    "Table containing averaged SPX performance over the last 50, 40, 30, 20, 10 years. "
                    "Each value is calculated as close of the last month and close of the current month.",
                    style=text_center,
                ),
                self.dropdown("select month", "this_next_month"),
                html.Div(id="monthly_first", style={"width": "80%", **table_center}),
                html.Br(),
                # FIRST GRAPH DAILY
                html.H2("Today's SPX seasonality", style=text_center),
                html.P(
                    "Each value is calculated as close of the last day and close of the current day",
                    style=text_center,
                ),
                self.dropdown("select day", "this_next_day"),
                html.Div(id="daily_first", style={"width": "80%", **table_center}),
                html.Br(),
                html.Br(),
                html.H2("PART 2: ALL HISTORICAL DATA", style=text_center),
                html.P(
                    [
                        "Graph below shows yearly % gains over the selected years. Since the average daily gains fluctuate a lot"
                        " from day to day, the graph shows smoothed line by 7 day moving average.",
                        html.Br(),
                        "You can choose different year periods. This will influence the rest of the page",
                    ],
                    style=text_center,
                ),
                # DROPDOWN + GRAPH
                self.dropdown(
                    "Select SPX performance period",
                    "slct",
                    [
                        {"label": "10 years", "value": 10},
                        {"label": "20 years", "value": 20},
                        {"label": "30 years", "value": 30},
                        {"label": "40 years", "value": 40},
                        {"label": "50 years", "value": 50},
                    ],
                    50,
                ),
                dcc.Graph(id="spx_graph", figure={}, style={"height": "90vh"}),
                # MONTHLY TABLE
                html.H2(id="monthly_title", style=text_center),
                html.P(
                    "Table containing averaged SPX performance over the selected years grouped monthly. Each value is calculated "
                    "as close of the last month and close of the current month",
                    style=text_center,
                ),
                html.Div(id="table_monthly", style={"width": "80%", **table_center}),
                html.Br(),
                # DAILY TABLE
                html.H2(id="daily_title", style=text_center),
                html.P(
                    "Table containing averaged SPX performance over the selected years grouped by every day. Each value is "
                    "calculated as close of the last day and close of the current day",
                    style=text_center,
                ),
                self.dropdown(
                    "Select Month",
                    "pick_month",
                    [{"label": st, "value": st} for st in months],
                ),
                html.Div(id="table_daily", style={"width": "80%", **table_center}),
                html.P("@Richard Volčko", style={"text-align": "right"}),
            ]
        )

    def dropdown(self, txt, _id, options=None, value=None):
        args = {
            "id": _id,
            "multi": False,
            "searchable": False,
            "style": {"width": "40%", "verticalAlign": "middle"},
        }
        if options:
            args["options"] = options
        if value:
            args["value"] = value

        return html.Div(
            [
                html.Div(
                    [
                        html.H4(
                            txt, style={"margin-right": "1.5em", "margin-top": "1.2em"}
                        )
                    ]
                ),
                dcc.Dropdown(**args),
            ],
            style=dropdown_center,
        )

    def transform_pandas(self, df, daily_month=0):
        if daily_month:
            df = df[df.index.str.contains(daily_month)]
            if_query = {
                "if": {
                    "filter_query": f'{{Day}}="{time_eastern()[0]}-{time_eastern()[1]}"'
                }
            }
        else:
            if_query = {"if": {"filter_query": f'{{Month}}="{time_eastern()[0]}"'}}

        df = df.reset_index(level=0)
        data = df.to_dict("records")

        columns = [
            {
                "name": i,
                "id": i,
            }
            for i in df.columns
        ]
        current_page = (
            (int(time_eastern()[1]) + 1) // 12
            if daily_month == time_eastern()[0]
            else 0
        )
        return dt.DataTable(
            data=data,
            columns=columns,
            style_cell={"textAlign": "center", "border": "1px solid grey"},
            style_data_conditional=[
                {
                    **if_query,
                    "backgroundColor": "lightblue",
                }
            ],
            # style_data={'border': '1px solid blue'},
            style_header={
                "border": "1px solid black",
                "backgroundColor": "lightgrey",
                "padding": "1.4rem 1rem",
                "font-size": "16px",
            },
            page_size=12,
            page_current=current_page,
        )

    def first_table(self, df, this_next):
        res = []

        for y in 50, 40, 30, 20, 10:
            if "-" in this_next:
                res.append(
                    {
                        "Period": f"{y} years",
                        "Day": this_next,
                        **df[y].loc[this_next].to_dict(),
                    }
                )
            else:
                res.append(
                    {
                        "Period": f"{y} years",
                        "Month": this_next,
                        **df[y].loc[this_next].to_dict(),
                    }
                )

        columns = [
            {
                "name": i,
                "id": i,
            }
            for i in res[0]
        ]
        return dt.DataTable(
            data=res,
            columns=columns,
            style_cell={"textAlign": "center", "border": "1px solid grey"},
            style_header={
                "border": "1px solid black",
                "backgroundColor": "lightgreen",
                "padding": "1.4rem 1rem",
                "font-size": "16px",
            },
        )

    def update(self, this_next_month, this_next_day, option, daily_month):
        debug_msg(f"OPTION: {option}")
        monthly_transform = self.transform_pandas(monthly_data[option])
        daily_transform = self.transform_pandas(daily_data[option], daily_month)

        monthly_first = self.first_table(monthly_data, this_next_month)
        daily_first = self.first_table(daily_data, this_next_day)

        return monthly_first, daily_first, monthly_transform, daily_transform


""" UPDATE HTML DROPDOWNS """


@app.callback(
    Output("this_next_month", "options"),
    Output("this_next_day", "options"),
    Output("this_next_month", "value"),
    Output("this_next_day", "value"),
    Output("pick_month", "value"),
    [
        Input("this_next_month", "value"),
        Input("this_next_day", "value"),
        Input("pick_month", "value"),
    ],
)
def update_date_dropdown(*inp):
    outs = [
        [time_eastern()[0], time_eastern()[2]],
        [
            f"{time_eastern()[0]}-{time_eastern()[1]}",
            f"{time_eastern()[3]}-{time_eastern()[4]}",
        ],
    ]
    if not inp[0]:
        inp = [i[0] for i in outs]
        inp.append(time_eastern()[0])

    return *[[{"label": i, "value": i} for i in out] for out in outs], *inp


""" Connect Plotly and Dash """


@app.callback(
    [
        Output("spx_graph", "figure"),
        Output("monthly_first", "children"),
        Output("daily_first", "children"),
        Output("table_monthly", "children"),
        Output("table_daily", "children"),
        Output("monthly_title", "children"),
        Output("daily_title", "children"),
        Input(component_id="this_next_month", component_property="value"),
        Input(component_id="this_next_day", component_property="value"),
        Input(component_id="slct", component_property="value"),
        Input(component_id="pick_month", component_property="value"),
    ]
)
def update_graph(*inp):

    out = page.update(*inp)

    table_title1 = f"Monthly SPX average gains table (over last {inp[2]} years)"
    table_title2 = f"Daily SPX average gains table (over last {inp[2]} years)"

    return fig[inp[2]], *out, table_title1, table_title2


def datas_thread():
    global fig, monthly_data, daily_data, safe

    fig = {}
    monthly_data = {}
    daily_data = {}
    loop_time = 3600
    safe = 0

    while True:
        st = time.time()
        try:
            for y in 10, 20, 30, 40, 50:
                fig[y], monthly_data[y], daily_data[y] = generate_graph.main(y)

        except Exception:
            traceback.print_exc()

        safe = 1

        time_took = time.time() - st
        if time_took < loop_time:
            time.sleep(loop_time - (time_took) + 0.1)
        else:
            print(f"Update Datas loop took too long: {round(time_took, 2)}s")


if __name__ == "__main__":

    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    safe = 0
    threading.Thread(target=datas_thread, daemon=True).start()

    page = Webpage()
    page.start_server()
