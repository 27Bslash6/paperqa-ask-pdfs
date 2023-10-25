import os
from pathlib import Path
from cachetools.func import lru_cache, ttl_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    CACHE_TYPE: str = Field(default="sqlite", env="CACHE_TYPE")
    DOCS_BASE_PATH: Path = Field(default=Path("docs"), env="DOCS_BASE_PATH")
    PROMPT_HISTORY_FILE: str = Field(default=".history.txt", env="PROMPT_HISTORY_FILE")
    HASHES_FILE_NAME: str = Field(default=".ask.hashes", env="HASHES_FILE_NAME")
    DATA_FILE_NAME: str = Field(default=".ask.joblib", env="DATA_FILE_NAME")
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
    Cached credentials lookups
    """
    return CredentialsFactory.create(type)
