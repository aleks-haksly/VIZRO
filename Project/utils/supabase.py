import os
from sqlalchemy import text
from sqlalchemy import create_engine
import pandas as pd
from utils import env_add


engine = create_engine(os.environ.get("supabase"), client_encoding='utf8', )

def select(sql):
    sql = text(sql)
    return pd.read_sql(sql, engine)

