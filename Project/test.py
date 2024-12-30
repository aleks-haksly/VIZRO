
from vizro import Vizro
import vizro.models as vm
import vizro.plotly.express as px
from vizro.figures import kpi_card
from vizro.figures import kpi_card_reference
from vizro.managers import data_manager
from include.supabase import select
import pandas as pd


df = select("SELECT * FROM vizro.yandex_data_agg")

def get_kpi_data(data=df, platform="touch", scale="day"):
        match scale:
            case 'day':
                return pd.DataFrame([df.groupby(["platform", "date"])["count"].sum().loc[platform].tail(2).to_list()], columns=["previous", "actual"])
            case 'hour':
                return pd.DataFrame([df.groupby(["platform", "date", "hour"])["count"].sum().loc[platform].tail(2).to_list()], columns=["previous", "actual"])


data_manager["kpi_data_day_touch"] = get_kpi_data(platform="touch", scale="day")
data_manager["kpi_data_day_desk"] = get_kpi_data(platform="desktop", scale="day")
data_manager["kpi_data_hour_touch"] = get_kpi_data(platform="touch", scale="hour")
data_manager["kpi_data_hour_desk"] = get_kpi_data(platform="desktop", scale="hour")

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
                title="Platforms ratio"
            ),
        ),
        ],
    layout=vm.Layout(grid=[[0, 1, 2,],]),
)

page_overview_day = vm.Page(
    title="Day scale data",
    layout=vm.Layout(grid=[[0,]]),
    components=[kpi_banner_day],
)

page_overview_hour = vm.Page(
    title="Hour scales data",
    layout=vm.Layout(grid=[[0,]]),
    components=[kpi_banner_hour],
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