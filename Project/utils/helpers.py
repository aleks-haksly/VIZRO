import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_pie_data(df):
    """Prepare data for the pie chart."""
    return df[['ds', 'platform', 'count', 'scale']]

def make_forecast(
    df, freq, platform, periods=0, daily_seasonality=True, 
    weekly_seasonality=True, yearly_seasonality=False, interval_width=0.95
):
    """Generate forecast using Prophet."""
    df = (
        df.query("scale == 'hours' & platform == @platform")
          [['ds', 'count']]
          .rename(columns={'count': 'y'})
          .reset_index()
    )
    model = Prophet(
        daily_seasonality=daily_seasonality, 
        weekly_seasonality=weekly_seasonality, 
        yearly_seasonality=yearly_seasonality, 
        interval_width=interval_width
    )
    model.fit(df)
    future = model.make_future_dataframe(freq=freq, periods=periods)
    forecast = model.predict(future)
    forecast['y'] = df['y']
    for col in ['yhat', 'yhat_lower']:
        forecast[col] = forecast[col].clip(lower=0.0)
    return forecast

def get_kpi_data(df, platform="touch"):
    """Prepare data for KPI visualization."""
    result = (
        df.query("platform == @platform")
          .rename(columns={"count": "actual"})
          .sort_values(by=['scale', 'ds'])
    )
    result["previous"] = result.groupby('scale')["actual"].shift(1)
    return result

def get_heatmap_data(df):
    """Prepare data for heatmap visualization."""
    df = df.query("scale == 'hours'").reset_index(drop=True)
    df['date'] = df.ds.dt.date
    df['hour'] = df.ds.dt.hour
    df["dow"] = df.ds.dt.weekday + 1
    df = df.sort_values(by='ds')
    df["wow_diff"] = df['count'] - df.groupby(["platform", "dow", "hour"])["count"].shift(1)
    return df[["date", "platform", "hour", "dow", "wow_diff"]]
