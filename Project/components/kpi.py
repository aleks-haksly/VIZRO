import vizro.models as vm
from vizro.figures import kpi_card_reference


def get_kpi_data(df, platform="touch"):
    d = df.groupby(["platform"], as_index=False)["count"].sum().rename(columns={"count": "actual"})
    d["previous"] = d["actual"].shift(1)
    return d.query("platform==@platform")

