from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    SERVICE_NAME: str = "Flat price statistic"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 5000

    DEBUG: bool = True

    DB_NAME: str = "ads"
    DB_URL: str = "mongodb://localhost:27018/"

    DEFAULT_CITIES = ("Санкт-Петербург", "Москва", "Екатеринбург")
    PARSE_PERIOD: int = 5 * 60
    COORDS = {
        "Санкт-Петербург": [59.6, 30.2],
        "Москва": [55.5, 37.4],
        "Екатеринбург": [56.5, 60.35],
    }
