import vizro.plotly.express as px
from vizro import Vizro
import vizro.models as vm
from include.supabase import select
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from vizro.models.types import capture

WEEK_DAYS = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}

df = select("SELECT * FROM vizro.yandex_data_agg")
plot_data = df.groupby(["platform", "ds", "weekday", "weekend"], as_index=False)["count"].sum()


@capture("graph")
def butterfly(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    data_frame["weekday"] = data_frame["weekday"].replace(WEEK_DAYS)

    fig = px.line(data_frame, **kwargs)

    weekend_ranges = []
    weekend_data = data_frame[data_frame["weekend"] == True]

    # Определяем интервалы выходных
    for date in weekend_data["ds"]:
        weekend_ranges.append((date, date + pd.Timedelta(days=1)))

    weekend_fillcolor = "rgba(128, 0, 128, 0.2)"  # заливка для выходных

    for start, end in weekend_ranges:
        fig.add_shape(
            type="rect",
            x0=start,
            x1=end,
            y0=0,
            y1=max(plot_data["count"]),
            fillcolor=weekend_fillcolor,
            layer="below",
            line_width=0
        )
    fig.add_trace(go.Scatter(
        x=[None],  # Фиктивные данные
        y=[None],
        mode="markers",
        marker=dict(size=10, color=weekend_fillcolor),  # Цвет совпадает с заливкой
        name="weekends"
    ))
    return fig

fig = butterfly(
    plot_data,
    x="ds", y="count", color="platform", hover_data="weekday")

page = vm.Page(
    title="My first dashboard",
    components=[
        vm.Graph(figure=fig),
        #vm.Graph(figure=px.histogram(df, x="sepal_width", color="species")),
    ],
    controls=[
        vm.Filter(column="platform", selector=vm.Dropdown(value=["ALL"])),
    ],
)

dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()