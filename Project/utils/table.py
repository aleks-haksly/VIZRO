from utils.supabase import select
from statsmodels.stats.proportion import proportions_chisquare
import pandas as pd
import vizro.models as vm
from vizro.tables import dash_ag_grid
from utils.data_loader import data_manager
# SQL-запрос


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


# Настройки стилей
CELL_STYLE = {
    "styleConditions": [
        {
            "condition": "params.value < 0.05",
            "style": {"backgroundColor": "#21ba06"},
        },
    ]
}



def proportions_chi2(row: pd.Series) -> float:
    """
    Вычисляет p-value для статистики хи-квадрат.
    """
    _, pval, _ = proportions_chisquare(
        count=[row['cnt_desktop'], row['cnt_touch']],
        nobs=[row['platform_total_desktop'], row['platform_total_touch']]
    )
    return pval

def get_table_data(sql=SQL_TEMPLATE, min_cnt=50, range=['2021-09-08', '2021-09-21']) -> pd.DataFrame:
  start_date, end_date = range
  sql = SQL_TEMPLATE.format(start_date=start_date, end_date=end_date, min_cnt=min_cnt)
  query_df = select(sql)
  query_df['pct_desktop'] = query_df['count_desktop'] / query_df['desktop_total']
  query_df['pct_touch'] = query_df['count_touch'] / query_df['touch_total']
  query_df["pval"] = query_df.apply(proportions_chi2, axis=1)
  return query_df.rename(columns={"count_desktop":"Count_desktop", "count_touch":"Count touch",
                                  "pct_desktop":"Count desktop %", "pct_touch":"Count touch %",
                                  "pval": "P-value"})




data_manager['df_pivoted'] = get_table_data

