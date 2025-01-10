import pandas as pd
import vizro.models as vm
from vizro.figures import kpi_card_reference, kpi_card
import vizro.plotly.express as px
from utils.data_loader import  get_kpi_data, get_pie_data, agg_data, data_manager
from vizro.models.types import capture
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from sqlalchemy import text
from sqlalchemy import create_engine
import pandas as pd
from vizro.managers import data_manager
from utils import env_add


# Page Overview Dashboard
## KPI container

fig_kpi_date = vm.Figure(
    id="kpi-date",
    figure=kpi_card(
        agg_data,
        value_column='ds',
        value_format='{value}',
        agg_func='max',
        title='Date',
        icon="calendar_month"
    ),
)

fig_kpi_touch = vm.Figure(
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
        )

fig_kpi_desk = vm.Figure(
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
        )


fig_graph_pie = vm.Graph(
            figure=px.pie(
                data_frame=get_pie_data(agg_data),
                values="count",
                names="platform",
                title="Queries Ratio Over Selected Date Range"
            ),
        )
## Outliers line chart

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

# Page heatmap

@capture("graph")
def heatmap_plot(data_frame: pd.DataFrame, z, **kwargs) -> go.Figure:
    df = data_frame[data_frame.date > data_frame.date.max() - pd.Timedelta(7, 'days')]
    if z == 'count':
        fig = px.density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",
                    text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                              color_continuous_scale=px.colors.sequential.Purples,
                              **kwargs
                              #hover_data ={'dow': True}
                              )


    else:
        fig = px.density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",
                              text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                              color_continuous_scale=px.colors.diverging.BrBG, color_continuous_midpoint=0,
                              **kwargs
                              )

    for data in fig.data:
        if z == 'wow_diff_%':
            data.hovertemplate = '<b>Date: </b>%{x}<br><b>Hour: </b>%{y}<br><b>Queries count: </b>%{z:.2f}%<extra></extra>'
            data.texttemplate = '%{z:.2f}%'
            fig.update_coloraxes(colorbar_ticksuffix= '%')
        else:
            data.hovertemplate = '<b>Date: </b>%{x}<br><b>Hour: </b>%{y}<br><b>Queries count: </b>%{z}<extra></extra>'
    fig.update_coloraxes(colorbar_title_text='')
    return fig

@capture("graph")
def butterfly(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    fig = px.bar(data_frame, **kwargs)

    orientation = fig.data[0].orientation
    x_or_y = "x" if orientation == "h" else "y"

    fig.update_traces({f"{x_or_y}axis": f"{x_or_y}2"}, selector=1)
    fig.update_layout({f"{x_or_y}axis2": fig.layout[f"{x_or_y}axis"]})
    fig.update_layout(
        {
            f"{x_or_y}axis": {"autorange": "reversed", "domain": [0, 0.5]},
            f"{x_or_y}axis2": {"domain": [0.5, 1]},
        }
    )

    if orientation == "h":
        fig.add_vline(x=0, line_width=2, line_color="grey")
    else:
        fig.add_hline(y=0, line_width=2, line_color="grey")
    fig.data[0].hovertemplate = '%{hovertext}% of all=%{x:.2%}qty=%{customdata[0]}'
    fig.data[0].name = 'desktop'
    fig.data[1].hovertemplate = '%{hovertext}% of all=%{x:.2%}qty=%{customdata[1]}'
    fig.data[1].name = 'touch'
    fig.update_yaxes(categoryorder='min ascending')

    return fig
