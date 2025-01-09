from vizro import Vizro
import pandas as pd
import vizro.plotly.express as px
import vizro.models as vm

from vizro.managers import data_manager

def load_iris_data(number_of_points=10):
    iris = pd.read_csv("../iris.csv")
    return iris.sample(number_of_points)

data_manager["iris"] = load_iris_data

page = vm.Page(
    title="Update the chart on page refresh",
    components=[
        vm.Graph(id="graph", figure=px.box("iris", x="variety", y="petal.width", color="variety"))
    ],
    controls=[
        vm.Parameter(
            targets=["graph.data_frame.number_of_points"],
            selector=vm.Slider(min=10, max=100, step=10, value=10),
        )
    ],
)

dashboard = vm.Dashboard(pages=[page])

Vizro().build(dashboard).run()