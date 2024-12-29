"""Dev app to try things out."""

import pandas as pd
from dash import Input, Output, callback
import vizro.models as vm
import vizro.plotly.express as px
from vizro import Vizro
from vizro.models.types import capture


df = px.data.iris()

vm.Page.add_type("controls", vm.RadioItems)

page = vm.Page(
    title="Page Title",
    components=[
        vm.Graph(
            id="graph_1",
            figure=px.scatter(df, x=None, y="sepal_length", color="species"),
            title = '123'
        )
    ],
    controls=[
        vm.RadioItems(
            title="Select item:",
            id="item_selector",
            options=["sepal", "petal"],
            value="sepal",
        ),
        vm.Parameter(
            targets=["graph_1.x"],
            selector=vm.Dropdown(
                title="Select x:",
                id="x_selector",
                multi=False,
                options=["sepal_width", "sepal_length"],
                value="sepal_width"
            )
        )
    ]
)

dashboard = vm.Dashboard(pages=[page])


# Pure dash callback to update x_selector options based on item_selector value
@callback(
    Output("x_selector", "options"),
    Output("x_selector", "value"),
    Input("item_selector", "value")
)
def update_parameter_options(selected_item):
    if selected_item == "sepal":
        options = ["sepal_width", "sepal_length"]
    else:
        options = ["petal_width", "petal_length"]
    return options, options[1],


if __name__ == "__main__":
    Vizro().build(dashboard).run()