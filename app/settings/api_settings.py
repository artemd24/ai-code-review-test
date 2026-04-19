import os

from pydantic import BaseSettings
from dotenv import load_dotenv

from app.settings.paths import DOT_ENV_PATH

load_dotenv(DOT_ENV_PATH)


class APISettings(BaseSettings):
    ADS_TOKEN = os.environ.get("ADS_TOKEN")
    ADATA_TOKEN = os.environ.get("ADATA_TOKEN")

    MAIL = os.environ.get("EMAIL")

    ADS_API_URL = "https://ads-api.ru/main/api"
    DADATA_API_URL = (
        "https://suggestions.dadata.ru/suggestions/api/4_1/rs/geolocate/address?"
    )

    AUTHORIZED_ADS_API_URL = f"{ADS_API_URL}?user={MAIL}&token={ADS_TOKEN}&param[2313]"

    Y_LABEL_MAPPING = {
        "psm": "Цена за квадратный метр (руб/кв.метр)",
        "area": "Метраж (кв метров)",
    }
