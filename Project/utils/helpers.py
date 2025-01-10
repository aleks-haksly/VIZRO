# Import necessary libraries
import pandas as pd
import vizro.models as vm
from vizro.figures import kpi_card_reference, kpi_card
import vizro.plotly.express as px
from utils.data_loader import get_kpi_data, get_pie_data, agg_data, data_manager
from vizro.models.types import capture
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from sqlalchemy import text
from sqlalchemy import create_engine
from utils import env_add

# Page Overview Dashboard
# KPI Container Definitions

# KPI for the latest date
fig_kpi_date = vm.Figure(
    id="kpi-date",
    figure=kpi_card(
        agg_data,  # Aggregated data
        value_column='ds',  # Value to display
        value_format='{value}',  # Formatting of the value
        agg_func='max',  # Aggregate function (max date)
        title='Date',  # Title of the KPI
        icon="calendar_month"  # Icon for the KPI
    ),
)

# KPI for Touch Queries with reference comparison (current vs. previous)
fig_kpi_touch = vm.Figure(
    id="kpi-touch",
    figure=kpi_card_reference(
        get_kpi_data(agg_data, "touch"),  # Get data for touch queries
        value_column="actual",  # Current value
        reference_column="previous",  # Previous value for comparison
        agg_func=lambda x: x.iloc[-1],  # Aggregation function (take last value)
        title="Touch Queries",  # Title of the KPI
        value_format="{value:,.0f}",  # Format current value
        reference_format="{delta_relative:+.1%} vs. previous ({reference:,.0f})",  # Format reference value
        icon=["Smartphone"],  # Icon for the KPI
    ),
)

# KPI for Desktop Queries with reference comparison (current vs. previous)
fig_kpi_desk = vm.Figure(
    id="kpi-desk",
    figure=kpi_card_reference(
        get_kpi_data(agg_data, "desktop"),  # Get data for desktop queries
        value_column="actual",  # Current value
        reference_column="previous",  # Previous value for comparison
        agg_func=lambda x: x.iloc[-1],  # Aggregation function (take last value)
        title="Desktop Queries",  # Title of the KPI
        value_format="{value:,.0f}",  # Format current value
        reference_format="{delta_relative:+.1%} vs. previous ({reference:,.0f})",  # Format reference value
        icon=["computer"],  # Icon for the KPI
    ),
)

# Pie chart showing the ratio of touch vs. desktop queries
fig_graph_pie = vm.Graph(
    figure=px.pie(
        data_frame=get_pie_data(agg_data),  # Get pie chart data
        values="count",  # Values for pie slices
        names="platform",  # Names of the categories
        title="Queries Ratio Over Selected Date Range",  # Title of the pie chart
    )
)


## Outliers Line Chart: Visualizing Outliers

@capture("graph")
def outliers_line_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Creates a line plot to visualize outliers based on prediction confidence intervals."""
    fig = go.Figure()

    # Add actual data trace
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['y'], name="Actual", mode='markers',
        customdata=data_frame['ds'].dt.day_name(),  # Add day of the week as custom data
        hovertemplate="<b>Date:</b> %{x}<br><b>Actual:</b> %{y}<br><b>DOW:</b> %{customdata}<extra></extra>",
        # Hover template
    ))

    # Add prediction data trace
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat'], name="Prediction", mode='lines',
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>Prediction:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
        # Hover template
    ))

    # Add 95% confidence interval lower bound
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat_lower'], fill='tonexty', mode='none', name="95% CI Lower",
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>95% CI Lower:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
        # Hover template
    ))

    # Add 95% confidence interval upper bound
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['yhat_upper'], fill='tonexty', mode='none', name="95% CI Upper",
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>95% CI Upper:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
        # Hover template
    ))

    # Add trend data trace
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['trend'], name="Trend"))

    fig.update_layout(
        yaxis=dict(title="Number of Queries"),  # Y-axis title
        title="Outliers Outside the 95% Confidence Interval"  # Chart title
    )
    return fig


## Components Plot: Trend and Seasonality

@capture("graph")
def components_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Creates subplots for trend and seasonality components."""
    fig = make_subplots(
        rows=3, cols=1,  # Three rows for subplots
        subplot_titles=["Trend", "Weekly Seasonality", "Daily Seasonality"]  # Titles for subplots
    )

    # Add trend trace
    fig.add_trace(go.Scatter(
        x=data_frame['ds'], y=data_frame['trend'], mode='lines', name='Trend',
        hovertemplate="<b>Date:</b> %{x}<br><b>Trend:</b> %{y:.0f}<extra></extra>",
    ), row=1, col=1)

    # Add weekly seasonality trace (last 168 data points)
    fig.add_trace(go.Scatter(
        x=data_frame['ds'][-168:], y=data_frame['weekly'][-168:], mode='lines', name='Weekly Trend',
        customdata=data_frame['ds'].dt.day_name(),
        hovertemplate="<b>Date:</b> %{x}<br><b>Weekly Trend:</b> %{y:.0f}<br><b>DOW:</b> %{customdata}<extra></extra>",
    ), row=2, col=1)

    # Add daily seasonality trace (last 24 data points)
    fig.add_trace(go.Scatter(
        x=data_frame['ds'][-24:], y=data_frame['daily'][-24:], mode='lines', name='Daily Trend',
        hovertemplate="<b>Time:</b> %{x}<br><b>Daily Trend:</b> %{y:.0f}<extra></extra>",
    ), row=3, col=1)

    fig.update_layout(title="Model Components", showlegend=False)  # Update layout with title
    return fig


# Page Heatmap: Visualizing Query Counts by Date and Hour

@capture("graph")
def heatmap_plot(data_frame: pd.DataFrame, z, **kwargs) -> go.Figure:
    """Creates a heatmap to visualize query data by date and hour."""
    # Filter the data for the last 7 days
    df = data_frame[data_frame.date > data_frame.date.max() - pd.Timedelta(7, 'days')]

    # Generate heatmap depending on whether we are visualizing count or percentage difference
    if z == 'count':
        fig = px.density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",  # Heatmap with query count
                                 text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                                 color_continuous_scale=px.colors.sequential.Purples,
                                 **kwargs)
    else:
        fig = px.density_heatmap(df, x="date", y="hour", z=z, histfunc="sum",  # Heatmap with percentage differences
                                 text_auto=True, nbinsy=24, nbinsx=7, facet_col="platform",
                                 color_continuous_scale=px.colors.diverging.BrBG, color_continuous_midpoint=0,
                                 **kwargs)

    # Format hover information based on the data type (count or percentage)
    for data in fig.data:
        if z == 'wow_diff_%':
            data.hovertemplate = '<b>Date: </b>%{x}<br><b>Hour: </b>%{y}<br><b>Queries count: </b>%{z:.2f}%<extra></extra>'
            data.texttemplate = '%{z:.2f}%'
            fig.update_coloraxes(colorbar_ticksuffix='%')  # Add percentage sign
        else:
            data.hovertemplate = '<b>Date: </b>%{x}<br><b>Hour: </b>%{y}<br><b>Queries count: </b>%{z}<extra></extra>'

    fig.update_coloraxes(colorbar_title_text='')  # Update colorbar title
    return fig


## Butterfly Plot: Comparing Desktop vs. Touch Queries

@capture("graph")
def butterfly(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Creates a butterfly chart comparing desktop vs. touch queries."""
    fig = px.bar(data_frame.iloc[::-1], color_discrete_sequence=px.colors.qualitative.D3[1::-1], **kwargs)

    # Reverse axis orientation for mirrored chart
    orientation = fig.data[0].orientation
    x_or_y = "x" if orientation == "h" else "y"

    fig.update_traces({f"{x_or_y}axis": f"{x_or_y}2"}, selector=1)
    fig.update_layout({f"{x_or_y}axis2": fig.layout[f"{x_or_y}axis"]})
    fig.update_layout(
        {
            f"{x_or_y}axis": {"autorange": "reversed", "domain": [0, 0.5]},  # Reverse axis for first plot
            f"{x_or_y}axis2": {"domain": [0.5, 1]},  # Reverse axis for second plot
        }
    )

    # Add vertical or horizontal line to separate the two data sets
    if orientation == "h":
        fig.add_vline(x=0, line_width=2, line_color="grey")
    else:
        fig.add_hline(y=0, line_width=2, line_color="grey")

    # Hover template and other plot adjustments
    fig.data[0].hovertemplate = '<b>%{hovertext}</b><br><b>part of all</b>=%{x:.2%}<br><b>qty</b>=%{customdata[0]}'
    fig.data[0].name = 'desktop'
    fig.data[1].hovertemplate = '<b>%{hovertext}</b><br><b>part of all</b>=%{x:.2%}<br><b>qty</b>=%{customdata[1]}'
    fig.data[1].name = 'touch'
    fig.update_yaxes(categoryorder='min ascending')  # Order the categories in ascending order
    fig.update_layout(
        title={
            'text': "Most popular queries in selected date range",  # Main plot title
            'x': 0.5,  # Center the title
            'xanchor': 'center'})
    return fig


## Line Chart for Queries by Hour

@capture("graph")
def linechart_query_plot(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    """Creates a line chart showing queries by hour for each platform."""
    fig = px.line(
        data_frame,
        x='hour',  # Hour of the day
        y='count',  # Query count
        color='query',  # Different queries
        facet_row='platform',  # Split by platform
        **kwargs
    )

    # Add plot title and adjust layout
    fig.update_layout(
        title={
            'text': "Dynamics in number of popular search queries by hour",  # Title
            'x': 0.5,  # Center title
            'xanchor': 'center',
            'yanchor': 'top'
        },
        legend=dict(
            orientation="h",  # Horizontal legend
            xanchor="center",  # Center the legend
            x=0.5
        )
    )

    # Automatically adjust subplot titles based on facet_row
    fig.for_each_annotation(lambda a: a.update(text=f"Platform: {a.text}"))

    return fig
