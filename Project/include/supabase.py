import os
from sqlalchemy import text
from sqlalchemy import create_engine
import pandas as pd
from include import env_add


engine = create_engine(os.environ.get("supabase"), client_encoding='utf8', )

def select(sql):
    sql = text(sql)
    return pd.read_sql(sql, engine)


# запросим предагреггированные данные
sql = """
SELECT
  card as client_id,
  Max((SELECT max(datetime) :: date FROM apteka.bonuscheques) - datetime :: date) as days_passed,
  count(*) as cnt,
  sum(summ_with_disc) as summ
FROM
  apteka.bonuscheques
GROUP BY
  card
"""
data = select(sql)

