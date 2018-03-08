from django.conf import settings
from sqlalchemy import create_engine

user = settings.DATABASES['default']['USER']
password = settings.DATABASES['default']['PASSWORD']
database_name = settings.DATABASES['default']['NAME']

database_url = 'postgresql://{user}:{password}@45.32.249.71:5432/{database_name}'.format(
    user='arbiter',
    password='porjectargogo!',
    database_name=,
)

engine = create_engine(database_url, echo=False)
df.to_sql(HistoricalPrices, con=engine, if_exists=append, index=False)
