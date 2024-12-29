from vizro import Vizro
import vizro.models as vm
from vizro.figures import kpi_card
from include._charts import FlexContainer
from vizro.figures import kpi_card_reference
from include.supabase import select
import pandas as pd

df = select("SELECT * FROM vizro.yandex_data_agg")
kpi_desk_day = pd.DataFrame([df.query("platform == 'desktop'").groupby("date")["count"].sum().tail(2).to_list()], columns=["previous", "actual"])
kpi_touch_day = pd.DataFrame([df.query("platform == 'touch'").groupby("date")["count"].sum().tail(2).to_list()], columns=["previous", "actual"])
kpi_desk_hour = pd.DataFrame([df.query("platform == 'desktop'").groupby(["date", "hour"])["count"].sum().tail(2).to_list()], columns=["previous", "actual"])
kpi_touch_hour = pd.DataFrame([df.query("platform == 'touch'").groupby(["date", "hour"])["count"].sum().tail(2).to_list()], columns=["previous", "actual"])

kpi_banner = vm.Container(
    components=[
        vm.Figure(
            id="kpi-touch-day",
            figure=kpi_card_reference(
                kpi_touch_day,
                value_column="actual",
                reference_column="previous",
                title="DoD queries - touch",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["Smartphone", "calendar_month"],
            ),
        ),
        vm.Figure(
            id="kpi-desk-day",
            figure=kpi_card_reference(
                kpi_desk_day,
                value_column="actual",
                reference_column="previous",
                title="DoD queries - desktop ",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous day ({reference:.0f})",
                icon=["computer", "calendar_month"],
            ),
        ),
        vm.Figure(
            id="kpi-touch-hour",
            figure=kpi_card_reference(
                kpi_touch_hour,
                value_column="actual",
                reference_column="previous",
                title="HoH queries - touch",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous hour ({reference:.0f})",
                icon=["Smartphone",  "Pace"],
            ),
        ),
        vm.Figure(
            id="kpi-desk-hour",
            figure=kpi_card_reference(
                kpi_desk_hour,
                value_column="actual",
                reference_column="previous",
                title="HoH queries - desktop ",
                value_format="{value:.0f}",
                reference_format="{delta_relative:+.1%} vs. previous hour ({reference:.0f})",
                icon=["computer", "Pace"],
            ),
        ),
        ],
    title = "",
    layout=vm.Layout(grid=[[0, 1, 2, 3],]),
)
page = vm.Page(
    title="My first dashboard",
    layout=vm.Layout(grid=[[0,]]),
    components=[kpi_banner])
dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()