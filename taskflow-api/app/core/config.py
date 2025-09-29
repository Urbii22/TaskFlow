from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "taskflow"
    ENV: str = "dev"
    DEBUG: bool = True
    SECRET_KEY: str = "change_me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "taskflow"
    POSTGRES_USER: str = "taskflow"
    POSTGRES_PASSWORD: str = "taskflow"

    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
