import snowflake.connector
import pandas as pd
from ydata_profiling import ProfileReport

# Snowflake Connection
def get_snowflake_connection():
    conn = snowflake.connector.connect(
        user='ArtjomsB',
        password='AH3kPakQwTjbMS7',
        account='emutive-jm11302',
        warehouse='COVID_WH',
        database='COVID19_EPIDEMIOLOGICAL_DATA',
        schema='PUBLIC'
    )
    return conn

# Query Snowflake
def query_snowflake(country=None, province=None, limit=100):
    conn = get_snowflake_connection()
    query = "SELECT * FROM JHU_COVID_19"
    
    conditions = []
    if country:
        conditions.append(f"country_region = '{country}'")
    if province:
        conditions.append(f"province_state = '{province}'")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" LIMIT {limit}"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df.to_dict(orient="records")

# Automated EDA Report
def generate_eda_report(df, filename="covid19_eda_report.html"):
    profile = ProfileReport(df, title="COVID-19 Dataset EDA Report", explorative=True)
    profile.to_file(filename)
    return filename
