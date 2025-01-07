from vizro import Vizro
import pandas as pd
import vizro.models as vm
from vizro.managers import data_manager
from utils.supabase import select
from vizro.figures import kpi_card_reference, kpi_card
from vizro.models.types import capture
import plotly.graph_objects as go
import vizro.plotly.express as px
from plotly.subplots import make_subplots
from utils.helpers import get_pie_data, make_forecast, get_kpi_data, get_heatmap_data
from plotly.express import density_heatmap

# Data Retrieval
agg_data = select("SELECT * FROM vizro.yandex_data_agg")

# Forecast Data Management
data_manager['forecast_touch'] = make_forecast(agg_data, freq='h', platform='touch')
data_manager['forecast_desktop'] = make_forecast(agg_data, freq='h', platform='desktop')
data_manager['heatmap_data'] = get_heatmap_data(agg_data)


# Plot functions

@capture("graph")
def outliers_line_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Create line plot to visualize outliers."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['y'], name="Actual", mode='markers',
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>Actual:</b> %{y}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat'], name="Prediction", mode='lines',
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>Prediction:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat_lower'], fill='tonexty', mode='none', name="95% CI Lower",
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>95% CI Lower:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat_upper'], fill='tonexty', mode='none', name="95% CI Upper",
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>95% CI Upper:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['trend'], name="Trend"))
    fig.update_layout(
        yaxis=dict(title="Number of Queries"),
        title="Outliers Outside the 95% Confidence Interval"
    )
    return fig

@capture("graph")
def components_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Create subplots for trend and seasonality components."""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=["Trend", "Weekly Seasonality", "Daily Seasonality"]
    )
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['trend'], mode='lines', name='Trend',
        hovertemplate="<b>Date:</b> %{x}<br><b>Trend:</b> %{y:.0f}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=data_frame['ds'][-168:], y=data_frame['weekly'][-168:], mode='lines', name='Weekly Trend',
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>Weekly Trend:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=data_frame['ds'][-24:], y=data_frame['daily'][-24:], mode='lines', name='Daily Trend',
        hovertemplate="<b>Time:</b> %{x}<br><b>Daily Trend:</b> %{y:.0f}<extra></extra>",
    ), row=3, col=1)
    fig.update_layout(title="Model Components", showlegend=False)
    return fig

@capture("graph")
def heatmap_plot(data_frame: pd.DataFrame, z, **kwargs) -> go.Figure:
    df = data_frame[data_frame.date > data_frame.date.max() - pd.Timedelta(7, 'days')]
    if z == 'count':
        fig = density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",
                    text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                              color_continuous_scale=px.colors.sequential.Purples, hover_data ={'dow': True}
                              )


    else:
        fig = density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",
                              text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                              color_continuous_scale=px.colors.diverging.BrBG, color_continuous_midpoint=0,
                              )

    for d in fig.data:
        d.hovertemplate = '<b>Date: </b>%{x}<br><b>Hour: </b>%{y}<br><b>Queries count: </b>%{z}<extra></extra>'

    return fig

# KPI Container
kpi_container = vm.Container(
    id="kpi_container",
    title="",
    components=[
        vm.Figure(
            id="kpi-date",
            figure=kpi_card(
                agg_data,
                value_column='ds',
                value_format='{value}',
                agg_func='max',
                title='Date',
                icon="calendar_month"
            ),
        ),
        vm.Figure(
            id="kpi-touch",
            figure=kpi_card_reference(
                get_kpi_data(agg_data, "touch"),
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="Touch Queries",
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
                title="Desktop Queries",
                value_format="{value:,.0f}",
                reference_format="{delta_relative:+.1%} vs. previous ({reference:,.0f})",
                icon=["computer"],
            ),
        ),
        vm.Graph(
            figure=px.pie(
                data_frame=get_pie_data(agg_data),
                values="count",
                names="platform",
                title="Queries Ratio Over Selected Date Range"
            ),
        ),
    ],
    layout=vm.Layout(grid=[[0, 1, 2, 3]])
)



# Line Charts Tabbed Component
line_charts_tabbed = vm.Tabs(
    tabs=[
        vm.Container(
            title="Outlier Detection - Touch",
            components=[
                vm.Graph(id="forecast_graph_touch", figure=outliers_line_plot('forecast_touch')),
                vm.Graph(id="forecast_components_touch", figure=components_plot('forecast_touch'))
            ],
            layout=vm.Layout(grid=[[0, 0, 1]])
        ),
        vm.Container(
            title="Outlier Detection - Desktop",
            components=[
                vm.Graph(id="forecast_graph_desktop", figure=outliers_line_plot('forecast_desktop')),
                vm.Graph(id="forecast_components_desktop", figure=components_plot('forecast_desktop'))
            ],
            layout=vm.Layout(grid=[[0, 0, 1]])
        ),
    ]
)

# Pages
page_overview = vm.Page(
    title="Overview Dashboard",
    layout=vm.Layout(grid=[[0], [1], [1], [1]]),
    components=[kpi_container, line_charts_tabbed],
    controls=[
        vm.Filter(
            column="scale",
            targets=[],
            selector=vm.RadioItems(
                title="Select Scale",
                id="scale_selector",
                options=['hours', 'days', 'weeks'],
                value='days'
            )
        ),
        vm.Filter(
            column="ds",
            targets=[],
            selector=vm.DatePicker(
                range=True,
                title="Dates",
                id='dates_selector_p1'
            )
        ),
    ]
)

# Overview Page

heatmap_tabbed = vm.Tabs(
    tabs=[vm.Container(
            title="Weekly queries count",
            components=[
            vm.Graph(
            id="Weekly queries count",
            figure= heatmap_plot('heatmap_data', z="count")
            )]),
            vm.Container(
            title="WoW difference",
            components=[
            vm.Graph(
            id="WoW difference",
            figure=heatmap_plot('heatmap_data', z="wow_diff")
            )])
        ])

page_queries_detailed = vm.Page(
    title="Queries",
    layout=vm.Layout(grid=[[0],]),
    components=[heatmap_tabbed, ],
    controls=[
        vm.Filter(
            column="ds",
            targets=[],
            selector=vm.DatePicker(
                range=True,
                title="Dates",
                id='dates_selector_p2'
            )
        ),
    ]
)

# Dashboard Setup
dashboard = vm.Dashboard(
    title="Yandex Queries Overview",
    pages=[page_overview, page_queries_detailed],
    navigation=vm.Navigation(
        nav_selector=vm.NavBar(
            items=[
                vm.NavLink(
                    label="Overview",
                    pages={"Sections": ["Overview Dashboard", "Queries"]},
                    icon="bar_chart_4_bars"
                )
            ]
        )
    )
)

Vizro().build(dashboard).run()
