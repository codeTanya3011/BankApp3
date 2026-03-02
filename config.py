import os
from dotenv import load_dotenv

load_dotenv()


POSTGRES_USER = os.getenv('DB_USER')
POSTGRES_PASSWORD = os.getenv('DB_PASSWORD')
POSTGRES_ADDRESS = os.getenv('DB_ADDRESS')
POSTGRES_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT')

TEST_POSTGRES_NAME = os.getenv('TEST_DB_NAME')


DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}:{DB_PORT}/{POSTGRES_NAME}"
)

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}:{DB_PORT}/{TEST_POSTGRES_NAME}"
)