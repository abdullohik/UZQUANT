from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    database_path: Path
    raw_data_dir: Path
    rse_universe_url: str="https://uzse.uz/asking_prices"
    request_timeout_seconds: float=30.0
    retry_attempts: int=3
    retry_backoff_seconds: float=1.0
    @classmethod
    def from_env(cls):
        return cls(Path(os.getenv("UZQUANT_DATABASE_PATH","data/uzquant.sqlite3")),Path(os.getenv("UZQUANT_RAW_DATA_DIR","data/raw")),request_timeout_seconds=float(os.getenv("UZQUANT_REQUEST_TIMEOUT","30")),retry_attempts=int(os.getenv("UZQUANT_RETRY_ATTEMPTS","3")),retry_backoff_seconds=float(os.getenv("UZQUANT_RETRY_BACKOFF","1")))
