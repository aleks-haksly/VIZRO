import pandas as pd
from vizro.managers import data_manager
from prophet import Prophet
from utils.supabase import select
from statsmodels.stats.proportion import proportions_chisquare


# Transformer Functions

def get_kpi_data(df, platform="touch"):
    """
    Prepare data for KPI visualization by filtering for a specific platform
    and calculating the previous period's actual values.
    """
    result = (
        df.query("platform == @platform")
          .rename(columns={"count": "actual"})
          .sort_values(by=['scale', 'ds'])
    )
    result["previous"] = result.groupby('scale')["actual"].shift(1)
    return result


def get_pie_data(df):
    """
    Prepare data for the pie chart by selecting relevant columns.
    """
    return df[['ds', 'platform', 'count', 'scale']]


def make_forecast(
    df, freq, platform, periods=0, daily_seasonality=True,
    weekly_seasonality=True, yearly_seasonality=False, interval_width=0.95
):
    """
    Generate a forecast using the Prophet library for a specified platform and frequency.
    """
    filtered_df = (
        df.query("scale == 'hours' & platform == @platform")
          [['ds', 'count']]
          .rename(columns={'count': 'y'})
          .reset_index(drop=True)
    )
    model = Prophet(
        daily_seasonality=daily_seasonality,
        weekly_seasonality=weekly_seasonality,
        yearly_seasonality=yearly_seasonality,
        interval_width=interval_width
    )
    model.fit(filtered_df)
    future = model.make_future_dataframe(freq=freq, periods=periods)
    forecast = model.predict(future)

    # Add historical values and ensure no negative predictions
    forecast['y'] = filtered_df['y']
    for col in ['yhat', 'yhat_lower']:
        forecast[col] = forecast[col].clip(lower=0.0)

    return forecast


def get_heatmap_data(df):
    """
    Prepare data for heatmap visualization by adding date, hour, and
    week-over-week difference calculations.
    """
    filtered_df = df.query("scale == 'hours'").reset_index(drop=True)
    filtered_df['date'] = filtered_df.ds.dt.date
    filtered_df['hour'] = filtered_df.ds.dt.hour
    filtered_df["dow"] = filtered_df.ds.dt.weekday + 1
    filtered_df = filtered_df.sort_values(by='ds')
    filtered_df['previous'] = filtered_df.groupby(["platform", "dow", "hour"])["count"].shift(1)
    filtered_df["wow_diff"] = filtered_df['count'] - filtered_df['previous']
    filtered_df["wow_diff_%"] = filtered_df["wow_diff"] * 100 / filtered_df['previous']

    return filtered_df[["ds", "date", "platform", "hour", "count", "wow_diff", "wow_diff_%"]]


# SQL Queries

SQL_TEMPLATE = """
WITH t as (
    SELECT
        query,
        platform,
        count(*) AS cnt,
        SUM(count(*)::int) OVER (PARTITION BY query) AS query_total,
        SUM(count(*)::int) OVER (PARTITION BY platform) AS platform_total
    FROM
        vizro.yandex_data yd
    WHERE
        ts BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        query, platform
)
SELECT 
    query,
    SUM(CASE WHEN platform = 'desktop' THEN cnt ELSE 0 END)::int AS count_desktop,
    SUM(CASE WHEN platform = 'touch' THEN cnt ELSE 0 END)::int AS count_touch,
    MAX(CASE WHEN platform = 'desktop' THEN platform_total ELSE 0 END) AS desktop_total,
    MAX(CASE WHEN platform = 'touch' THEN platform_total ELSE 0 END) AS touch_total
FROM t
WHERE t.query_total >= {min_cnt}
GROUP BY query
"""


def proportions_chi2(row: pd.Series) -> float:
    """
    Calculate the p-value for the Chi-squared test for proportions.
    """
    _, pval, _ = proportions_chisquare(
        count=[row['count_desktop'], row['count_touch']],
        nobs=[row['desktop_total'], row['touch_total']]
    )
    return pval


def get_table_data(sql=SQL_TEMPLATE, min_cnt=50, date_range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
    """
    Fetch and prepare data for the summary table, including Chi-squared p-values.
    """
    start_date, end_date = date_range
    sql = sql.format(start_date=start_date, end_date=end_date, min_cnt=min_cnt)
    query_df = select(sql)
    query_df['pct_desktop'] = query_df['count_desktop'] / query_df['desktop_total']
    query_df['pct_touch'] = query_df['count_touch'] / query_df['touch_total']
    query_df["pval"] = query_df.apply(proportions_chi2, axis=1)

    return query_df.rename(columns={
        "count_desktop": "Count desktop",
        "count_touch": "Count touch",
        "pct_desktop": "Count desktop %",
        "pct_touch": "Count touch %",
        "pval": "P-value"
    })


def get_butterfly_data(sql=SQL_TEMPLATE, min_cnt=50, date_range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
    """
    Fetch and prepare data for the butterfly chart by selecting top queries.
    """
    start_date, end_date = date_range
    sql = sql.format(start_date=start_date, end_date=end_date, min_cnt=min_cnt)
    query_df = select(sql)

    # Select top 10 queries for each platform
    top_desktop = query_df.sort_values(by="count_desktop", ascending=False).head(10)
    top_touch = query_df.sort_values(by="count_touch", ascending=False).head(10)

    query_df = pd.concat([top_desktop, top_touch], axis=0).drop_duplicates(subset=['query'])
    query_df['pct_desktop'] = query_df['count_desktop'] / query_df['desktop_total']
    query_df['pct_touch'] = query_df['count_touch'] / query_df['touch_total']

    return query_df


# Line Chart Query Data

SQL_TEMPLATE_QUERY_LINECHART = """
WITH t AS (
    SELECT
        query,
        date_part('hour', ts) AS hour,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (PARTITION BY date_part('hour', ts) ORDER BY COUNT(*) DESC) AS rnb
    FROM
        vizro.yandex_data yd
    WHERE
        ts BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY query, date_part('hour', ts)
)
SELECT 
    platform, 
    date_part('hour', ts) AS hour, 
    query, 
    COUNT(*) 
FROM 
    vizro.yandex_data yd 
WHERE 
    query IN (SELECT DISTINCT query FROM t WHERE rnb < 6)
GROUP BY 
    platform, date_part('hour', ts), query
"""


def get_query_linechart_data(date_range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
    """
    Fetch and prepare data for query linechart visualization.
    """
    start_date, end_date = date_range
    sql = SQL_TEMPLATE_QUERY_LINECHART.format(start_date=start_date, end_date=end_date)
    return select(sql)


# Data Management

agg_data = select("SELECT * FROM vizro.yandex_data_agg")
data_manager['forecast_touch'] = make_forecast(agg_data, freq='h', platform='touch')
data_manager['forecast_desktop'] = make_forecast(agg_data, freq='h', platform='desktop')
data_manager['heatmap_data'] = get_heatmap_data(agg_data)
data_manager["data_table"] = get_table_data
data_manager['butterfly_data'] = get_butterfly_data
data_manager['query_linechart_data'] = get_query_linechart_data
