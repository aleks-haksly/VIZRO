from vizro import Vizro
import pandas as pd
import vizro.models as vm
from vizro.managers import data_manager
from vizro.tables import dash_ag_grid
from include.supabase import select
from vizro.figures import kpi_card_reference

agg_data = select("SELECT * FROM vizro.yandex_data_aggs")


def get_kpi_data(df, platform="touch"):

    d = df.query("platform==@platform").rename(columns={"count": "actual"}).sort_values(by=['scale', 'ts'])
    d["previous"] = d.groupby('scale')["actual"].shift(1)
    print(d)
    return d



kpi_container = vm.Container(
    id="kpi_container",
    title="",
    components=[
        vm.Figure(
            id="kpi-touch",
            figure=kpi_card_reference(
                get_kpi_data(agg_data, "touch"),
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
            id="kpi-desk",
            figure=kpi_card_reference(
                get_kpi_data(agg_data, "desktop"),
                value_column="actual",
                reference_column="previous",
                agg_func=lambda x: x.iloc[-1],
                title="DoD queries - desktop",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["computer"],
            ),
        ),

        ],
    layout=vm.Layout(grid=[[0, 1, ],]),
)



page_overview = vm.Page(
    title="Overview dashboard",
    layout=vm.Layout(grid=[[0],[1]]),
    components=[kpi_container, vm.AgGrid(figure=dash_ag_grid(data_frame=agg_data))],
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
                    label="Main",
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


