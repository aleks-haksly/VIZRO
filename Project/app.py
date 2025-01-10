from vizro import Vizro
from dash import dcc
import pandas as pd
import vizro.models as vm
from dash import Input, Output, callback
from vizro.models.types import capture
import plotly.graph_objects as go
import vizro.plotly.express as px
from plotly.subplots import make_subplots
from plotly.express import density_heatmap
from vizro.tables import dash_ag_grid
from utils.helpers import outliers_line_plot, components_plot, heatmap_plot, fig_kpi_date, fig_kpi_touch, fig_kpi_desk, fig_graph_pie, butterfly, linechart_query_plot
from utils.supabase import select
from utils.data_loader import data_manager
from utils.table import get_table_data

# Overview page
## KPI Container with multiple graphs
kpi_container = vm.Container(
    id="kpi_container",
    title="",
    components=[fig_kpi_date, fig_kpi_touch, fig_kpi_desk, fig_graph_pie],  # List of KPI figures
    layout=vm.Layout(grid=[[0, 1, 2, 3]])  # Grid layout for display
)

# Line Charts Tabbed Component for Outlier Detection
line_charts_tabbed = vm.Tabs(
    tabs=[
        # Touch Outlier Detection Tab
        vm.Container(
            title="Outlier Detection - Touch",
            components=[
                vm.Graph(id="forecast_graph_touch", figure=outliers_line_plot('forecast_touch')),  # Outlier plot
                vm.Graph(id="forecast_components_touch", figure=components_plot('forecast_touch'))  # Components plot
            ],
            layout=vm.Layout(grid=[[0, 0, 1]])  # Grid layout for this tab
        ),
        # Desktop Outlier Detection Tab
        vm.Container(
            title="Outlier Detection - Desktop",
            components=[
                vm.Graph(id="forecast_graph_desktop", figure=outliers_line_plot('forecast_desktop')),
                vm.Graph(id="forecast_components_desktop", figure=components_plot('forecast_desktop'))
            ],
            layout=vm.Layout(grid=[[0, 0, 1]])  # Grid layout for this tab
        ),
    ]
)

# Page Overview layout with KPI and Line Charts
page_overview = vm.Page(
    title="Overview Dashboard",
    layout=vm.Layout(grid=[[0], [1], [1], [1]]),
    components=[kpi_container, line_charts_tabbed],  # Adding components to the page
    controls=[
        # Filter for Scale
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
        # Date Range Filter
        vm.Filter(
            column="ds",
            targets=[],
            selector=vm.DatePicker(
                range=True,
                title="Dates range",
                id='dates_selector_p1'
            )
        ),
    ]
)

# Page Queries counts detailed with heatmap
heatmap_tabbed = vm.Tabs(
    tabs=[
        # Weekly Queries Count Tab
        vm.Container(
            title="Weekly queries count",
            components=[vm.Graph(id="Weekly queries count", figure=heatmap_plot('heatmap_data', z="count", title='Weekly queries count'))]
        ),
        # WoW Difference Tab
        vm.Container(
            title="WoW difference",
            components=[vm.Graph(id="WoW difference", figure=heatmap_plot('heatmap_data', z="wow_diff", title='WoW queries count difference'))]
        ),
        # WoW Difference % Tab
        vm.Container(
            title="WoW difference %",
            components=[vm.Graph(id="WoW % difference", figure=heatmap_plot('heatmap_data', z="wow_diff_%", title='WoW queries count difference %'))]
        )
    ]
)

# Queries counts detailed layout with tabs
page_queries_detailed = vm.Page(
    title="Queries counts detailed",
    layout=vm.Layout(grid=[[0],]),
    components=[heatmap_tabbed],
    controls=[
        # Date Range Filter for Queries Data
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

# Detailed Queries Text Page with table and charts
## Table configuration with specific column definitions and styles
CELL_STYLE = {
    "styleConditions": [
        {
            "condition": "params.value < 0.05",
            "style": {"backgroundColor": "#21ba06"},  # Style for P-value < 0.05
        },
    ]
}

COLUMN_DEFS = [
    {"field": "query"},
    {"field": "Count touch", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "Count touch %", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "Count desktop", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "Count desktop %", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "P-value", "valueFormatter": {"function": "d3.format(',.3f')(params.value)"}, "cellStyle": CELL_STYLE},
]

# Creating AgGrid for query data
table_grid = vm.AgGrid(
    id='ag',
    figure=dash_ag_grid(id='dag', data_frame='data_table', columnDefs=COLUMN_DEFS,
                         defaultColDef={"resizable": False, "filter": True, "editable": False},
                         dashGridOptions={"pagination": True, "paginationPageSize": 10},
                         columnSize="responsiveSizeToFit"),
    title="Queries counts and statistical significance of the difference between platforms",
)

# Butterfly Chart for platform percentage comparison
butterfly_chart = vm.Graph(id='btfly', figure=butterfly(
    'butterfly_data',
    x=["pct_desktop", "pct_touch"],
    y="query",
    labels={"value": "% of all", "variable": "platform:"},
    hover_name="query", hover_data={'query': False, 'count_desktop': True, 'count_touch': True},
))

# Line chart for query data
linechart_query_plot = vm.Graph(id='lchq', figure=linechart_query_plot('query_linechart_data'))

# Page layout for Queries Text Detailed
page_queries_text_detailed = vm.Page(
    title="Queries text detailed",
    layout=vm.Layout(grid=[[1, 2], [0, 2], [0, 2]]),
    components=[table_grid, butterfly_chart, linechart_query_plot],
    controls=[
        # Date Range Filter for Queries Text Data
        vm.Parameter(
            targets=["ag.data_frame.date_range", 'btfly.data_frame.date_range', 'lchq.data_frame.date_range'],
            selector=vm.DatePicker(
                range=True,
                title="Filter date range",
                id='date_filter',
                min='2021-09-01',
                max='2021-09-21',
                value=['2021-09-08', '2021-09-21']
            )
        ),
        # Slider to filter by minimum query count
        vm.Parameter(
            targets=["ag.data_frame.min_cnt", 'btfly.data_frame.min_cnt'],
            selector=vm.Slider(
                title="Filter min sum query counts",
                id='min_query_count_filter',
                min=20,
                max=200,
                step=20,
                value=100
            )
        ),
    ]
)

# Final Dashboard setup with multiple pages and navigation
dashboard = vm.Dashboard(
    title="Yandex Queries Overview",
    pages=[page_overview, page_queries_detailed, page_queries_text_detailed],
    navigation=vm.Navigation(
        nav_selector=vm.NavBar(
            items=[
                vm.NavLink(
                    label="Overview",
                    pages={"Sections": ["Overview Dashboard", "Queries counts detailed", "Queries text detailed"]},
                    icon="bar_chart_4_bars"
                )
            ]
        )
    )
)

# Running the dashboard with Vizro
Vizro().build(dashboard).run()
