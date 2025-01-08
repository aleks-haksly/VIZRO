from utils.supabase import select
from statsmodels.stats.proportion import proportions_chisquare
import pandas as pd
import vizro.models as vm
from vizro.tables import dash_ag_grid

SQL = """
SELECT
    platform,
	query,
	count(*) AS cnt,
	sum(count(query)) over(PARTITION BY platform) AS platform_total, 
	sum(count(query)) over(PARTITION BY query) AS query_count_total
FROM
	vizro.yandex_data yd
GROUP BY
	platform,
	query
"""
def proportions_chi2(df: pd.DataFrame):
    _, pval, _ = proportions_chisquare(
        count=[df['cnt_desktop'], df['cnt_touch']],
        nobs=[df['platform_total_desktop'], df['platform_total_touch']])
    return pval

def get_table_data(sql, min_cnt):
    min_query_cnt = min_cnt
    df = select(sql).query("query_count_total >= @min_query_cnt")
    df_pivoted = df.pivot(index='query', columns=["platform"], values=["cnt", "platform_total"], ).reset_index()
    df_pivoted.columns = ["_".join(a).rstrip('_') for a in df_pivoted.columns.to_flat_index()]
    df_pivoted.fillna(
    value={'cnt_touch': 0, 'cnt_desktop': 0, 'platform_total_desktop': df_pivoted['platform_total_desktop'].max(),
           'platform_total_touch': df_pivoted['platform_total_touch'].max()}, inplace=True)

    #df_pivoted.reset_index(inplace=True)
    df_pivoted["pval"] = df_pivoted.apply(lambda x: proportions_chi2(x), axis=1)
    df_pivoted['pct_desktop'] = df_pivoted['cnt_desktop'] / df_pivoted['platform_total_desktop']
    df_pivoted['pct_touch'] = df_pivoted['cnt_touch'] / df_pivoted['platform_total_touch']
    return df_pivoted

cellStyle = {
    "styleConditions": [
        {
            "condition": "params.value < 0.05",
            "style": {"backgroundColor": "#21ba06"},
        },
    ]
}

columnDefs = [
    {"field": "query"},
    {"field": "cnt_touch", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "pct_touch", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "cnt_desktop", "valueFormatter": {"function": "d3.format(',.0f')(params.value)"}},
    {"field": "pct_desktop", "valueFormatter": {"function": "d3.format(',.3%')(params.value)"}},
    {"field": "pval", "valueFormatter": {"function": "d3.format(',.3f')(params.value)"}, "cellStyle": cellStyle,},
]

table_pval = vm.AgGrid(
    figure=dash_ag_grid(
    data_frame=get_table_data(sql=SQL, min_cnt=100),
    columnDefs=columnDefs,
    defaultColDef={"resizable": False, "filter": True, "editable": False},
                    dashGridOptions={"pagination": True, "paginationPageSize": 20},
    ),
    title="Queries counts and statistical significance of the difference between platforms"
)



