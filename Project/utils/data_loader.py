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
SELECT
    platform,
    query,
    count(*) AS cnt,
    sum(count(query)) over(PARTITION BY platform) AS platform_total, 
    sum(count(query)) over(PARTITION BY query) AS query_count_total
FROM
    vizro.yandex_data yd
WHERE
    ts BETWEEN '{start_date}' AND '{end_date}'
GROUP BY
    platform, query
"""


def proportions_chi2(row: pd.Series) -> float:
    """
    Вычисляет p-value для статистики хи-квадрат.
    """
    _, pval, _ = proportions_chisquare(
        count=[row['cnt_desktop'], row['cnt_touch']],
        nobs=[row['platform_total_desktop'], row['platform_total_touch']]
    )
    return pval

def get_table_data(sql=SQL_TEMPLATE, min_cnt=50, range=['2021-09-01', '2021-09-21']) -> pd.DataFrame:
    """
    Получает данные из базы, фильтрует по минимальному количеству запросов и вычисляет статистические показатели.
    """
    start_date, end_date = range
    sql = SQL_TEMPLATE.format(start_date=start_date, end_date=end_date)
    df = select(sql).query("query_count_total >= @min_cnt")

    # Пивотирование данных
    df_pivoted = (
        df.pivot(index='query', columns="platform", values=["cnt", "platform_total"])
        .reset_index()
    )
    df_pivoted.columns = ["_".join(col).rstrip('_') for col in df_pivoted.columns.to_flat_index()]
    # Заполнение пропущенных значений
    max_totals = {
        'platform_total_desktop': df_pivoted['platform_total_desktop'].max(),
        'platform_total_touch': df_pivoted['platform_total_touch'].max()
    }
    df_pivoted.fillna(
        value={'cnt_touch': 0, 'cnt_desktop': 0, **max_totals},
        inplace=True
    )

    # Добавление вычисляемых колонок
    df_pivoted["pval"] = df_pivoted.apply(proportions_chi2, axis=1)
    df_pivoted['pct_desktop'] = df_pivoted['cnt_desktop'] / df_pivoted['platform_total_desktop']
    df_pivoted['pct_touch'] = df_pivoted['cnt_touch'] / df_pivoted['platform_total_touch']
    return df_pivoted




data_manager['df_pivoted'] = get_table_data





# Data Management

agg_data = select("SELECT * FROM vizro.yandex_data_agg")
data_manager['forecast_touch'] = make_forecast(agg_data, freq='h', platform='touch')
data_manager['forecast_desktop'] = make_forecast(agg_data, freq='h', platform='desktop')
data_manager['heatmap_data'] = get_heatmap_data(agg_data)
data_manager["data_table"] = get_table_data