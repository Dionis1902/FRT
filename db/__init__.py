import databases
import sqlalchemy
from config import DATABASE_URL
from db.models import metadata

database = databases.Database(DATABASE_URL)

engine = sqlalchemy.create_engine(DATABASE_URL, client_encoding='utf8')

metadata.create_all(engine)
