from vizro import Vizro
import pandas as pd
import vizro.models as vm
from vizro.managers import data_manager
from vizro.tables import dash_ag_grid
from include.supabase import select
from vizro.figures import kpi_card_reference, kpi_card
from prophet import Prophet
from vizro.models.types import capture
import plotly.graph_objects as go
import vizro.plotly.express as px
from plotly.subplots import make_subplots


agg_data = select("SELECT * FROM vizro.yandex_data_aggs")
def get_pie_data(df):
    return df[['ts', 'platform', 'count', 'scale']]

def make_forcast(df, freq, platform, periods=0, daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False, interval_width=0.95):
    df = df.query("scale == 'hours' & platform == @platform")[['ts', 'count']].rename(columns={'ts':'ds', 'count':'y'}).reset_index()
    model = Prophet(daily_seasonality=daily_seasonality, weekly_seasonality=weekly_seasonality, yearly_seasonality=yearly_seasonality, interval_width=interval_width,)
    model.fit(df)
    future = model.make_future_dataframe(freq=freq, periods=periods)
    forecast = model.predict(future)
    forecast['y'] = df['y']
    for col in ['yhat', 'yhat_lower']:
        forecast[col] = forecast[col].clip(lower=0.0)
    forecast['ts'] =  forecast['ds']
    print(forecast.columns)
    return forecast

@capture("graph")
def outliers_line_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['y'],  name="fact", mode='markers',
                             customdata=data_frame['ds'].dt.day_name(),
                             hovertemplate="<b>Date:</b> %{x}<br><b>Actual value %{y}<br>%{customdata}<extra></extra>",
                             ))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat'], name="predict", mode='lines',
                             customdata=data_frame['ds'].dt.day_name(),
                             hovertemplate="<b>Date:</b> %{x}<br><b>Predict:</b> %{y}<br>%{customdata}<extra></extra>",
                             ))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_lower'], fill='tonexty', mode='none', name="95% CI lower",
                             customdata=data_frame['ds'].dt.day_name(),
                             hovertemplate="<b>Date:</b> %{x}<br><b>95% CI lower:</b> %{y}<br>%{customdata}<extra></extra>",
                             ))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_upper'], fill='tonexty', mode='text', name="95% CI upper",
                             customdata=data_frame['ds'].dt.day_name(),
                             hovertemplate="<b>Date:</b> %{x}<br><b>95% CI Upper:</b> %{y}<br>%{customdata}<extra></extra>",
                             ))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['trend'], name="trend"))
    fig.update_layout(yaxis=dict(title=dict(text="Number of queries")), title=dict(text="Outliers outside the 95% confidence interval"),)

    return fig


@capture("graph")
def components_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    fig = make_subplots(rows=3, cols=1, subplot_titles=["Trend", "Weekly Seasonality", "Daily Seasonality"])
    fig.add_trace(
        go.Scatter(x=data_frame['ds'], y=data_frame['trend'], mode='lines', name='Trend',
                   hovertemplate="<b>Date:</b> %{x}<br><b>Trend:</b> %{y}<br><extra></extra>",),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=data_frame['ds'][-168:], y=data_frame['weekly'][-168:], mode='lines', name='Weekly trend',
                   customdata=data_frame['ds'].dt.day_name(),
                   hovertemplate="<b>Date:</b> %{x}<br><b>Weekly trend:</b> %{y}<br><b>DOW:</b>%{customdata}<extra></extra>",),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=data_frame['ds'][-24:], y=data_frame['daily'][-24:], mode='lines', name='Daily trend',
                   hovertemplate="<b>Time:</b> %{x}<br><b>Daily trend:</b> %{y}<br><extra></extra>",),
        row=3, col=1
    )
    fig.update_layout(title="Model Components", showlegend=False)

    return fig

def get_kpi_data(df, platform="touch"):

    result = df.query("platform==@platform").rename(columns={"count": "actual"}).sort_values(by=['scale', 'ts'])
    result["previous"] = result.groupby('scale')["actual"].shift(1)
    return result

kpi_container = vm.Container(
    id="kpi_container",
    title="",
    components=[
        vm.Figure(
            id="kpi-date",
            figure=kpi_card(
                agg_data,
                value_column='ts',
                value_format='{value}',
                agg_func='max',
                title='Date',
                icon="calendar_month"),
        ),
        vm.Figure(
            id="kpi-touch",
            figure=kpi_card_reference(
                get_kpi_data(agg_data, "touch"),
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="Touch queries",
                value_format="{value:,.0f}",
                reference_format="{delta_relative:+.1%} vs. previous ({reference:,.0f})",
                icon=["Smartphone"],

            ),
        ),
        vm.Figure(
            id="kpi-desk",
            figure=kpi_card_reference(
                get_kpi_data(agg_data, "desktop"),
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="Desktop queries",
                value_format="{value:,.0f}",
                reference_format="{delta_relative:+.1%} vs. previous ({reference:,.0f})",
                icon=["computer"],
            ),
        ),
            vm.Graph(
            figure=px.pie(
                data_frame = get_pie_data(agg_data),
                values="count",
                names="platform",
                title="Queries ratio over selected dates range"
            ),
        ),

        ],
    layout=vm.Layout(grid=[[0, 1, 2, 3],]),
)
data_manager['forcast_touch'] = make_forcast(agg_data, freq='h', platform='touch')
data_manager['forcast_desktop'] = make_forcast(agg_data, freq='h', platform='desktop')

line_charts_tabbed = vm.Tabs(
    tabs=[vm.Container(
            title="Outlier detection - touch",
            components=[
                vm.Graph(id="forcast_graph_touch", figure=outliers_line_plot('forcast_touch')),
                vm.Graph(id="forcast_components_touch", figure=components_plot('forcast_touch'))
            ],
            layout=vm.Layout(grid=[[0, 0, 1]])),
            vm.Container(
            title="Outlier detection - desktop",
            components=[vm.Graph(id="forcast_graph_desktop", figure=outliers_line_plot('forcast_desktop')),
                        vm.Graph(id="forcast_components_desktop", figure=components_plot('forcast_desktop'))],
            layout=vm.Layout(grid=[[0, 0, 1]])),
        ])

page_overview = vm.Page(
    title="Overview dashboard",
    layout=vm.Layout(grid=[[0],[1],[1],[1]]),
    components=[kpi_container, line_charts_tabbed],
    controls=[
        vm.Filter(column="scale",targets=[], selector=vm.RadioItems(title ="Select scale", id="scale_selector", options=['hours', 'days', 'weeks'], value='days')),
        vm.Filter(column="ts",targets=[], selector=vm.DatePicker(range=True, title ="Dates", id='dates_selector', )), #value=['2021-09-02', '2021-09-03']
    ],
)

dashboard = vm.Dashboard(
    title="Yandex queries overview",
    pages=[page_overview,],
    navigation=vm.Navigation(
        nav_selector=vm.NavBar(
            items=[
                vm.NavLink(
                    label="Overview",
                    pages={
                        "Sections": [
                            "Overview dashboard",

                        ],
                    },
                    icon="bar_chart_4_bars",
                ),
            ]
        )
    ),
)

Vizro().build(dashboard).run()


