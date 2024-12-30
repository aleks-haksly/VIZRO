from vizro import Vizro
import vizro.models as vm
import vizro.plotly.express as px
from vizro.figures import kpi_card
from vizro.figures import kpi_card_reference
from vizro.managers import data_manager
from include.supabase import select
import pandas as pd

df = select("SELECT * FROM vizro.yandex_data_agg")


def get_kpi_data(data=df, platform="touch", scale='day'):
    return lambda scale: pd.DataFrame([df.groupby(["platform", "date"])["count"].sum().loc[platform].tail(2).to_list()],
                                      columns=["previous", "actual"]) if scale == "day" else \
        pd.DataFrame([df.groupby(["platform", "date", "hour"])["count"].sum().loc[platform].tail(2).to_list()],
                     columns=["previous", "actual"])


data_manager["kpi_data_touch"] = get_kpi_data(platform="touch")
data_manager["kpi_data_desk"] = get_kpi_data(platform="desktop")
