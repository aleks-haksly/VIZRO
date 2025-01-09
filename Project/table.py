from include import env_add
from sqlalchemy import text
from sqlalchemy import create_engine
import pandas as pd
import os

sql = """
SELECT
    platform,
	query,
	count(*) AS cnt,
	sum(count(query)) over(PARTITION BY platform) AS platform_total, 
	sum(count(query)) over(PARTITION BY query) AS query_count_total
FROM
	vizro.yandex_data yd
	WHERE 
GROUP BY
	platform,
	query
"""

engine = create_engine(os.environ.get("supabase"), client_encoding='utf8', )


def select(sql):
    sql = text(sql)
    return pd.read_sql(sql, engine)


df = select(sql)
min_query_cnt = 50
df = df.query("query_count_total >= @min_query_cnt")
df_pivoted = df.pivot(index='query', columns=["platform"], values=["cnt", "platform_total"], ).reset_index()
df_pivoted.columns = ["_".join(a).rstrip('_') for a in df_pivoted.columns.to_flat_index()]
df_pivoted
df_pivoted.fillna(
    value={'cnt_touch': 0, 'cnt_desktop': 0, 'platform_total_desktop': df_pivoted['platform_total_desktop'].max(),
           'platform_total_touch': df_pivoted['platform_total_touch'].max()}, inplace=True)
df_pivoted

from statsmodels.stats.proportion import proportions_chisquare


def proportions_chi2(df: pd.DataFrame):
    _, pval, _ = proportions_chisquare(
        count=[df['cnt_desktop'], df['cnt_touch']],
        nobs=[df['platform_total_desktop'], df['platform_total_touch']])

    return pval


df_pivoted["pval"] = df_pivoted.apply(lambda x: proportions_chi2(x), axis=1)
df_pivoted['pct_desktop'] = df_pivoted['cnt_desktop'] / df_pivoted['platform_total_desktop']
df_pivoted['pct_touch'] = df_pivoted['cnt_touch'] / df_pivoted['platform_total_touch']

import vizro.models as vm
import vizro.plotly.express as px
from vizro import Vizro
from vizro.tables import dash_ag_grid

df = df_pivoted.reset_index()

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

page = vm.Page(
    title="Statisitical significencs in querries qty",
    components=[
        vm.AgGrid(
            title="Modified Dash AG Grid",
            figure=dash_ag_grid(
                data_frame=df,
                columnDefs=columnDefs,
                defaultColDef={"resizable": False, "filter": False, "editable": False},
                dashGridOptions={"pagination": True, "paginationPageSize": 20}
            ),
        )
    ],
)

dashboard = vm.Dashboard(pages=[page])

Vizro().build(dashboard).run()