import pandas as pd
from vizro.managers import data_manager
from prophet import Prophet
from utils.supabase import select
from statsmodels.stats.proportion import proportions_chisquare

# Transformer functions

def get_kpi_data(df, platform="touch"):
    """Prepare data for KPI visualization."""
    result = (
        df.query("platform == @platform")
          .rename(columns={"count": "actual"})
          .sort_values(by=['scale', 'ds'])
    )
    result["previous"] = result.groupby('scale')["actual"].shift(1)
    return result

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

def get_heatmap_data(df):
    """Prepare data for heatmap visualization."""
    df = df.query("scale == 'hours'").reset_index(drop=True)
    df['date'] = df.ds.dt.date
    df['hour'] = df.ds.dt.hour
    df["dow"] = df.ds.dt.weekday + 1
    df = df.sort_values(by='ds')
    df['previous'] = df.groupby(["platform", "dow", "hour"])["count"].shift(1)
    df["wow_diff"] = df['count'] - df['previous']
    df["wow_diff_%"] = df["wow_diff"] * 100 / df['previous']
    return df[["ds", "date", "platform", "hour", "count", "wow_diff", "wow_diff_%"]] #'dow' not used



SQL_TEMPLATE = """
WITH t as (
SELECT
    query,
    platform,
    count(*) AS cnt,
    sum(count(*)::int) OVER (PARTITION BY query) as query_total,
    sum(count(*)::int) OVER (PARTITION BY platform) as platform_total
FROM
    vizro.yandex_data yd
WHERE
    ts BETWEEN '{start_date}' AND '{end_date}'
GROUP BY
    query, platform)

SELECT 
    query,
    sum(case when platform = 'desktop' then cnt else 0 end)::int as count_desktop,
    sum(case when platform = 'touch' then cnt else 0 end)::int as count_touch,
    max(case when platform = 'desktop' then platform_total else 0 end) as desktop_total,
    max(case when platform = 'touch' then platform_total else 0 end) as touch_total
FROM t
    WHERE t.query_total >= {min_cnt}
GROUP BY query
"""


def proportions_chi2(row: pd.Series) -> float:
    """
    Вычисляет p-value для статистики хи-квадрат.
    """
    _, pval, _ = proportions_chisquare(
        count=[row['count_desktop'], row['count_touch']],
        nobs=[row['desktop_total'], row['touch_total']]
    )
    return pval

def get_table_data(sql=SQL_TEMPLATE, min_cnt=50, range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
  start_date, end_date = range
  sql = SQL_TEMPLATE.format(start_date=start_date, end_date=end_date, min_cnt=min_cnt)
  query_df = select(sql)
  query_df['pct_desktop'] = query_df['count_desktop'] / query_df['desktop_total']
  query_df['pct_touch'] = query_df['count_touch'] / query_df['touch_total']
  query_df["pval"] = query_df.apply(proportions_chi2, axis=1)
  return query_df.rename(columns={"count_desktop":"Count desktop", "count_touch":"Count touch",
                                  "pct_desktop":"Count desktop %", "pct_touch":"Count touch %",
                                  "pval": "P-value"})


def get_butterfly_data(sql=SQL_TEMPLATE, min_cnt=50, range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
  start_date, end_date = range
  sql = SQL_TEMPLATE.format(start_date=start_date, end_date=end_date, min_cnt=min_cnt)
  query_df = select(sql)
  query_df = pd.concat([query_df.sort_values(by="count_desktop", ascending=False).head(10),  query_df.sort_values(by="count_touch", ascending=False).head(10)], axis=0).drop_duplicates(subset=['query'])
  query_df['pct_desktop'] = query_df['count_desktop'] / query_df['desktop_total']
  query_df['pct_touch'] = query_df['count_touch'] / query_df['touch_total']

  return query_df







# Data Management

agg_data = select("SELECT * FROM vizro.yandex_data_agg")
data_manager['forecast_touch'] = make_forecast(agg_data, freq='h', platform='touch')
data_manager['forecast_desktop'] = make_forecast(agg_data, freq='h', platform='desktop')
data_manager['heatmap_data'] = get_heatmap_data(agg_data)
data_manager["data_table"] = get_table_data
data_manager['butterfly_data'] = get_butterfly_data