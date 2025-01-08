from utils.supabase import select
from statsmodels.stats.proportion import proportions_chisquare
import pandas as pd
import vizro.models as vm
from vizro.tables import dash_ag_grid

# SQL-запрос
SQL = """
SELECT
    platform,
    query,
    count(*) AS cnt,
    sum(count(query)) OVER (PARTITION BY platform) AS platform_total, 
    sum(count(query)) OVER (PARTITION BY query) AS query_count_total
FROM
    vizro.yandex_data yd
GROUP BY
    platform,
    query
"""

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

COLUMN_DEFS = [
    {"field": "query"},
    {"field": "cnt_touch", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "pct_touch", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "cnt_desktop", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "pct_desktop", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "pval", "valueFormatter": {"function": "d3.format(',.3f')(params.value)"}, "cellStyle": CELL_STYLE},
]

def proportions_chi2(row: pd.Series) -> float:
    """
    Вычисляет p-value для статистики хи-квадрат.
    """
    _, pval, _ = proportions_chisquare(
        count=[row['cnt_desktop'], row['cnt_touch']],
        nobs=[row['platform_total_desktop'], row['platform_total_touch']]
    )
    return pval

def get_table_data(sql: str, min_cnt: int) -> pd.DataFrame:
    """
    Получает данные из базы, фильтрует по минимальному количеству запросов и вычисляет статистические показатели.
    """
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


def create_table_with_filter(start_date, end_date):
    sql = SQL_TEMPLATE.format(start_date=start_date, end_date=end_date)
    data_frame = get_table_data(sql=sql, min_cnt=100)
    return vm.AgGrid(
        figure=dash_ag_grid(
            data_frame=data_frame,
            columnDefs=COLUMN_DEFS,
            defaultColDef={"resizable": False, "filter": True, "editable": False},
            dashGridOptions={"pagination": True, "paginationPageSize": 20},
        ),
        title="Queries counts and statistical significance of the difference between platforms"
    )





# Создание таблицы
table_pval = vm.AgGrid(
    id='tb1',
    figure=dash_ag_grid(
        data_frame=get_table_data(sql=SQL, min_cnt=100),
        columnDefs=COLUMN_DEFS,
        defaultColDef={"resizable": False, "filter": True, "editable": False},
        dashGridOptions={"pagination": True, "paginationPageSize": 20},
    ),
    title="Queries counts and statistical significance of the difference between platforms"
)