from operator import iconcat

from vizro import Vizro
import vizro.models as vm
import vizro.plotly.express as px
from vizro.figures import kpi_card
from vizro.figures import kpi_card_reference
from vizro.managers import data_manager
from include.supabase import select
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from vizro.models.types import capture


df = select("SELECT * FROM vizro.yandex_data_agg")
df["date"] = pd.to_datetime(df["ds"], format='%Y-%m_%d')
df["hour"] = df["ds"].dt.hour

def get_kpi_data(data=df, platform="touch", scale="day"):
        match scale:
            case 'day':
                d = df.groupby(["platform", "date"], as_index=False)["count"].sum().rename(columns={"count": "actual"})
                d["previous"] = d["actual"].shift(1)
                return d.query("platform==@platform")
            case 'hour':
                d = df.groupby(["platform", "date", "hour"], as_index=False)["count"].sum().rename(columns={"count": "actual"})
                d["previous"] = d["actual"].shift(1)
                return d.query("platform==@platform")

def make_forcast(df, freq, periods=0, daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False, interval_width=0.95):
    model = Prophet(daily_seasonality=daily_seasonality, weekly_seasonality=weekly_seasonality, yearly_seasonality=yearly_seasonality, interval_width=interval_width,)

    model.fit(df)
    future = model.make_future_dataframe(freq=freq, periods=periods)

    forecast = model.predict(future)
    forecast['y'] = df['y']
    for col in ['yhat', 'yhat_lower']:
        forecast[col] = forecast[col].clip(lower=0.0)
    return forecast

@capture("graph")
def outliers_line_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['y'],  name="fact", mode='markers'))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat'], name="predict", mode='lines'))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_upper'], fill='tonexty', mode='none', name="95% CI upper"))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat'], mode='lines', showlegend=False)),
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_lower'], fill='tonexty', mode='none', name="95% CI lower"))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['trend'], name="trend"))
    return fig



data_manager["kpi_data_day_touch"] = get_kpi_data(platform="touch", scale="day")
data_manager["kpi_data_day_desk"] = get_kpi_data(platform="desktop", scale="day")
data_manager["kpi_data_hour_touch"] = get_kpi_data(platform="touch", scale="hour")
data_manager["kpi_data_hour_desk"] = get_kpi_data(platform="desktop", scale="hour")
data_manager["pie"] = df.groupby(["date", "hour", "platform"], as_index=False)["count"].sum().tail(2)


kpi_banner_day = vm.Container(
    id="kpi_banner_day",
    title="",
    components=[
        vm.Figure(
            id="kpi-touch-day",
            figure=kpi_card_reference(
                "kpi_data_day_touch",
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="DoD queries - touch",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["Smartphone"],

            ),
        ),
        vm.Figure(
            id="kpi-desk-day",
            figure=kpi_card_reference(
                "kpi_data_day_desk",
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="DoD queries - desktop",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["computer"],
            ),
        ),
        vm.Graph(
            figure=px.pie(
                data_frame=df.groupby(["date", "platform"], as_index=False)["count"].sum().tail(2),
                values="count",
                names="platform",
                title="Platforms ratio"
            ),
        ),
        ],
    layout=vm.Layout(grid=[[0, 1, 2,],]),
)

kpi_banner_hour = vm.Container(
    id="kpi_banner_hour",
    title="",
    components=[
        vm.Figure(
            id="kpi-touch-hour",
            figure=kpi_card_reference(
                "kpi_data_hour_touch",
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="HoH queries - touch",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous hour ({reference:.0f})",
                icon=["Smartphone"],

            ),
        ),
        vm.Figure(
            id="kpi-desk-hour",
            figure=kpi_card_reference(
                "kpi_data_hour_desk",
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="HoH queries - desktop",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous hour ({reference:.0f})",
                icon=["computer"],
            ),
        ),
        vm.Graph(
            figure=px.pie(
                data_frame  = df.groupby(["date", "hour", "platform"], as_index=False)["count"].sum().tail(2),
                values="count",

                names="platform",
                title="123"
            ),
        ),
        ],
    layout=vm.Layout(grid=[[0, 1, 2,],]),
)



line_charts_tabbed = vm.Tabs(
    tabs=[vm.Container(
            title="touch",
            components=[
            vm.Graph(
            id="outliers_hour_touch",
            figure=outliers_line_plot(make_forcast(df.query("platform=='touch'")[["ds", "count"]].rename(columns={"count": "y"}).sort_values(by='ds').reset_index(), freq='h'))
            )]),
            vm.Container(
            title="desktop",
            components=[
            vm.Graph(
            id="outliers_hour_desk",
            figure=outliers_line_plot(make_forcast(df.query("platform=='desktop'")[["ds", "count"]].rename(columns={"count": "y"}).sort_values(by='ds').reset_index(), freq='h')
            ))
        ])])






page_overview_day = vm.Page(
    title="Day scale data",
    layout=vm.Layout(grid=[[0,]]),
    components=[kpi_banner_day],
    controls=[
        vm.Filter(column="date",targets=["kpi-touch-day", "kpi-desk-day"], selector=vm.DatePicker(range=True, title ="Dates")),
    ],
)

page_overview_hour = vm.Page(
    title="Hour scales data",
    layout=vm.Layout(grid=[[0,],[1,],[1,], [1,]]),
    components=[kpi_banner_hour, line_charts_tabbed],
    controls=[
        vm.Filter(column="date",
                  selector=vm.DatePicker(range=True, title="Dates")),
    ],
)

dashboard = vm.Dashboard(
    title="Vizro Features",
    pages=[page_overview_day, page_overview_hour],
    navigation=vm.Navigation(
        nav_selector=vm.NavBar(
            items=[
                #vm.NavLink(label="Homepage", pages=["Homepage"], icon="Home"),
                vm.NavLink(
                    label="Features",
                    pages={
                        "Scales": [
                            "Day scale data",
                            "Hour scales data",

                        ],
                    },
                    icon="Library Add",
                ),
            ]
        )
    ),
)

#dashboard = vm.Dashboard(pages=[page_overview_day, page_overview_hour])
Vizro().build(dashboard).run()