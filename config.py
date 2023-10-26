from functools import cached_property
import os
from pathlib import Path
from cachetools.func import lru_cache, ttl_cache
from pydantic import BaseSettings, Field

from platformdirs import PlatformDirs


class Settings(BaseSettings):
    APP_NAME: str = Field(default="ask", env="AKS_APP_NAME")
    APP_AUTHOR: str = Field(default="27bslash6", env="AKS_APP_AUTHOR")

    CACHE_TYPE: str = Field(default="sqlite", env="AKS_CACHE_TYPE")
    DOCS_BASE_PATH: Path = Field(default=Path("docs"), env="AKS_DOCS_BASE_PATH")
    PROMPT_HISTORY_FILE: str = Field(
        default=".history.txt", env="AKS_PROMPT_HISTORY_FILE"
    )
    HASHES_FILE_NAME: str = Field(default=".ask.hashes", env="AKS_HASHES_FILE_NAME")
    DATA_FILE_NAME: str = Field(default=".ask.joblib", env="AKS_DATA_FILE_NAME")
    CACHE_FILE_NAME: str = Field(default=".ask.cache", env="AKS_CACHE_FILE_NAME")
    ALLOWED_FILE_TYPES: list = Field(default=["md", "txt", "pdf", "doc", "docx"])

    DEFAULT_CONTEXT: str = Field(
        default="""
    You are an expert advisor with deep industry knowledge of the indexed content.
    """
    )
    DEFAULT_LENGTH_PROMPT: str = Field(
        default="up to 250 words", env="DEFAULT_LENGTH_PROMPT"
    )
    MAX_INDEXER_THREADS: int = Field(default=4, env="MAX_INDEXER_THREADS")
    MAX_SOURCES: int = Field(default=10, env="MAX_SOURCES")
    WORKING_DIR: Path = Field(default=Path(os.getcwd()), env="WORKING_DIR")

    @property
    def APP_VERSION(self) -> str:
        with open(f"{self.WORKING_DIR}/VERSION") as f:
            return f.read().strip()


@lru_cache(maxsize=1)
def get_settings_singleton() -> Settings:
    return Settings()


settings = get_settings_singleton()


class Credentials(BaseSettings):
    type: str


class CredentialsFactory:
    @staticmethod
    def create(type: str) -> Credentials:
        subclasses = Credentials.__subclasses__()
        for subclass in subclasses:
            if subclass.__name__.lower() == f"{type}credentials":
                return subclass(type=type)
        raise ValueError(f"Unknown credentials type: {type}")


@ttl_cache(300)
def get_credentials_singleton(type: str) -> Credentials:
    """
    Caches credentials lookups for 5 minutes to reduce I/O
    """
    return CredentialsFactory.create(type)


dirs = PlatformDirs(
    appname=settings.APP_NAME,
    appauthor=settings.APP_AUTHOR,
    version=settings.APP_VERSION,
)
