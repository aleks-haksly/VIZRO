import pandas as pd
import vizro.plotly.express as px
import vizro.models as vm
from vizro import Vizro

# Example DataFrame
data = {
    "date": pd.date_range(start="2024-12-01", periods=100, freq="D"),
    "platform": ["desktop", "touch"] * 50,
    "count": range(100),
}
df = pd.DataFrame(data)




# Create a Graph Component
last_values_graph = vm.Graph(
    id="last_values_graph",
    figure=px.bar(
        data_frame=df.groupby("platform", as_index=False).tail(1),  # Default: Last rows
        x="platform",
        y="count",
        title="Last Values by Platform",
    ),
)

# Add a Date Filter
date_filter = vm.Filter(column="date", targets=["last_values_graph"],     selector=vm.DatePicker(range=True, title="Select Date Range"))

# Create a Page with Filter and Graph
page_last_values = vm.Page(
    title="Last Values Overview",
    layout=vm.Layout(grid=[[0]]),
    components=[last_values_graph],
    controls=[date_filter],
)

# Build and Run Dashboard
dashboard = vm.Dashboard(
    title="Vizro Dashboard with Filterable Last Values",
    pages=[page_last_values],
)

Vizro().build(dashboard).run()
