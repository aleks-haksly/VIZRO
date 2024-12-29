
from vizro import Vizro
import vizro.models as vm
import vizro.plotly.express as px
from vizro.figures import kpi_card
from include._charts import FlexContainer
from vizro.figures import kpi_card_reference
from vizro.managers import data_manager
from include.supabase import select
import pandas as pd
from dash import Input, Output, callback

df = select("SELECT * FROM vizro.yandex_data_agg")

def get_kpi_data(data=df, platform="touch", scale='day'):
        return lambda scale: pd.DataFrame([df.groupby(["platform", "date"])["count"].sum().loc[platform].tail(2).to_list()], columns=["previous", "actual"]) if scale == "day" else \
                             pd.DataFrame([df.groupby(["platform", "date", "hour"])["count"].sum().loc[platform].tail(2).to_list()], columns=["previous", "actual"])

data_manager["kpi_data_touch"] = get_kpi_data(platform="touch")
data_manager["kpi_data_desk"] = get_kpi_data(platform="desktop")

kpi_banner = vm.Container(
    id="kpi_banner_container",
    title="",
    components=[
        vm.Figure(
            id="kpi-touch",
            figure=kpi_card_reference(
                "kpi_data_touch",
                value_column="actual",
                reference_column="previous",
                title="DoD queries - touch",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["Smartphone", "calendar_month"],

            ),
        ),
        vm.Figure(
            id="kpi-desk",
            figure=kpi_card_reference(
                "kpi_data_desk",
                value_column="actual",
                reference_column="previous",
                title="DoD queries - desktop",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["computer", "calendar_month"],
            ),
        ),
        vm.Graph(
            figure=px.pie(
                df, values="count", names="platform", title="Platforms ratio"
            ),
        ),
        ],
    layout=vm.Layout(grid=[[0, 1, 2,],]),
)
page = vm.Page(
    title="My first dashboard",
    layout=vm.Layout(grid=[[0,]]),
    components=[kpi_banner],
    controls=[
        vm.Parameter(
            targets=["kpi-touch.data_frame.scale", "kpi-desk.data_frame.scale", "kpi-touch.title"],
            selector=vm.RadioItems(title="Select scale:",
            id="scale_selector",
            options=["day", "hour"],
            value="day")
        )
    ],

)

dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()