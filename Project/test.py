import pandas as pd
import plotly.graph_objects as go

import vizro.models as vm
from vizro import Vizro
from vizro.models.types import capture


def waterfall_data():
    return pd.DataFrame(
        {
            "measure": ["relative", "relative", "total", "relative", "relative", "total"],
            "x": ["Sales", "Consulting", "Net revenue", "Purchases", "Other expenses", "Profit before tax"],
            "text": ["+60", "+80", "", "-40", "-20", "Total"],
            "y": [60, 80, 0, -40, -20, 0],
        }
    )


@capture("graph")
def waterfall(data_frame, measure, x, y, text, title=None):
    fig = go.Figure()
    fig.add_traces(
        go.Waterfall(
            measure=data_frame[measure],
            x=data_frame[x],
            y=data_frame[y],
            text=data_frame[text],
            decreasing={"marker": {"color": "#ff5267"}},
            increasing={"marker": {"color": "#08bdba"}},
            totals={"marker": {"color": "#00b4ff"}},
        ),
    )

    fig.update_layout(title=title)
    return fig


page_0 = vm.Page(
    title="Custom chart",
    components=[
        vm.Graph(
            figure=waterfall(data_frame=waterfall_data(), measure="measure", x="x", y="y", text="text"),
        ),
    ],
    # Apply a filter to the custom chart
    controls=[
        vm.Filter(column="x", selector=vm.Dropdown(title="Financial categories", multi=True)),
    ],
)
dashboard = vm.Dashboard(pages=[page_0])

Vizro().build(dashboard).run()