from vizro import Vizro
from dash import dcc
import pandas as pd
import vizro.models as vm
from dash import Input, Output, callback
#from vizro.managers import data_manager
#from utils.supabase import select
#from vizro.figures import kpi_card_reference, kpi_card
from vizro.models.types import capture
import plotly.graph_objects as go
import vizro.plotly.express as px
from plotly.subplots import make_subplots
#from utils.helpers import get_pie_data, make_forecast, get_kpi_data, get_heatmap_data
from plotly.express import density_heatmap
from vizro.tables import dash_ag_grid
#from utils.data_loader import data_manager, agg_data
from utils.helpers import outliers_line_plot, components_plot, heatmap_plot, fig_kpi_date, fig_kpi_touch, fig_kpi_desk, fig_graph_pie
from utils.supabase import select
from utils.data_loader import data_manager
from utils.table import  get_table_data
# Overview page
## Components
kpi_container = vm.Container(
    id="kpi_container",
    title="",
    components=[fig_kpi_date, fig_kpi_touch, fig_kpi_desk, fig_graph_pie],
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

## Page Overview layout
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
                title="Dates range",
                id='dates_selector_p1'
            )
        ),
    ]
)

# Page Queries counts detailed
## Components
heatmap_tabbed = vm.Tabs(
    tabs=[vm.Container(
            title="Weekly queries count",
            components=[
            vm.Graph(
            id="Weekly queries count",
            figure= heatmap_plot('heatmap_data', z="count", title = 'Weekly queries count')
            )]),
        vm.Container(
            title="WoW difference",
            components=[
            vm.Graph(
            id="WoW difference",
            figure=heatmap_plot('heatmap_data', z="wow_diff", title = 'WoW queries count difference')
            )]),
        vm.Container(
            title="WoW difference %",
            components=[
            vm.Graph(
            id="WoW % difference",
            figure=heatmap_plot('heatmap_data', z="wow_diff_%", title = 'WoW queries count difference %')
            )])
        ])
## Queries counts detailed layout
page_queries_detailed = vm.Page(
    title="Queries counts detailed",
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
# Detailed queries text page
## Components


# Настройки стилей
CELL_STYLE = {
    "styleConditions": [
        {
            "condition": "params.value < 0.05",
            "style": {"backgroundColor": "#21ba06"},
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


page_queries_text_detailed = vm.Page(
    title="Queries text detailed",
    layout=vm.Layout(grid=[[0],]),
    components=[
        vm.AgGrid(id='ag', figure=dash_ag_grid(id='dag', data_frame='data_table', columnDefs=COLUMN_DEFS,
                                               defaultColDef={"resizable": False, "filter": True, "editable": False},
                                               dashGridOptions={"pagination": True, "paginationPageSize": 20},
                                               ),title="Queries counts and statistical significance of the difference between platforms")
    ],
    controls=[
        vm.Parameter(
            targets=["ag.data_frame.range"],
            selector=vm.DatePicker(
                range=True,
                title="Filter date range",
                id='date_filter',
                min='2021-09-01',
                max='2021-09-21',
                value=['2021-09-08', '2021-09-21'])),

vm.Parameter(
            targets=["ag.data_frame.min_cnt"],
            selector=vm.Slider(
                title="Filter min sum query counts",
                id='min_query_count_filter',
                min=20,
                max=200,
                step=20,
                value=100
            )),
    ]
        )



# Dashboard Setup
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

Vizro().build(dashboard).run()
