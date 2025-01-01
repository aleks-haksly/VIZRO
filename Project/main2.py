import vizro.plotly.express as px
from vizro import Vizro
import vizro.models as vm
from include.supabase import select
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from vizro.models.types import capture
from prophet import Prophet


def make_forcast(df, periods, freq, hue, daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False, interval_width=0.95):
  frames = []
  for s in df[hue].unique():
    model = Prophet(daily_seasonality=daily_seasonality, weekly_seasonality=weekly_seasonality, yearly_seasonality=yearly_seasonality, interval_width=interval_width)
    model.fit(df.query(f"{hue} == '{s}'"))
    future = model.make_future_dataframe(freq=freq, periods=periods)
    forecast = model.predict(future)
    forecast[f"{hue}"] = f'{s}'
    forecast['y'] = df.query(f"{hue} == '{s}'").sort_values(by='ds')['y'].to_list()
    frames.append(forecast)
  return pd.concat(frames)

data = select("SELECT ds, count as y, platform FROM vizro.yandex_data_agg order by 1")
plot_data = make_forcast(data, 0, 'h', 'platform')


@capture("graph")
def butterfly(data_frame: pd.DataFrame, **kwargs) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['y'],  name="fact", mode='markers'))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat'], name="predict", mode='lines'))

    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_upper'], fill='tonexty', mode='none', name="95% CI upper"))
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat'], mode='lines', showlegend=False)),
    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['yhat_lower'], fill='tonexty', mode='none', name="95% CI lower"))

    fig.add_trace(go.Scatter(x=data_frame['ds'], y=data_frame['trend'], name="trend"))

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
        vm.Filter(column="platform", selector=vm.RadioItems()),
    ],
)

dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()