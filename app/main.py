# app/main.py
from functools import lru_cache
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import snowflake.connector
import pandas as pd
from pymongo import MongoClient
from prophet import Prophet

#  Hardcoded Credentials 
SNOWFLAKE_USER = "ArtjomsB"
SNOWFLAKE_PASSWORD = "AH3kPakQwTjbMS7"
SNOWFLAKE_ACCOUNT = "emutive-jm11302"
SNOWFLAKE_WAREHOUSE = "COVID_WH"
SNOWFLAKE_DATABASE = "COVID19_EPIDEMIOLOGICAL_DATA"
MONGO_URI = "mongodb+srv://artjominnbox:fxNQp9mGuhUPav8c@covid19project.bunrdt6.mongodb.net/"

#  Application Setup 
app = FastAPI(title="COVID-19 Project API")

#  Database Connections 
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["covid19_supplementary"]
comments_collection = db["comments"]

@lru_cache()
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER, password=SNOWFLAKE_PASSWORD, account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE, database=SNOWFLAKE_DATABASE, schema='PUBLIC'
    )

class Comment(BaseModel):
    country: str
    comment: str

#  API Endpoints 
@app.get("/")
def read_root():
    return {"message": "API is running. Go to /docs for documentation."}

@app.get("/api/countries")
@lru_cache(maxsize=1)
def get_countries_list():
    conn = get_snowflake_connection()
    df = pd.read_sql("SELECT DISTINCT COUNTRY_REGION FROM JHU_COVID_19 ORDER BY COUNTRY_REGION", conn)
    return {"countries": df['COUNTRY_REGION'].tolist()}

@app.get("/api/timeseries/{country}")
@lru_cache(maxsize=128)
def get_country_timeseries(country: str):
    conn = get_snowflake_connection()
    query = "SELECT DATE, CASE_TYPE, CASES FROM JHU_COVID_19 WHERE COUNTRY_REGION = %(country)s ORDER BY DATE"
    df = pd.read_sql(query, conn, params={'country': country})
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for country: {country}")
    df['DATE'] = pd.to_datetime(df['DATE']).dt.strftime('%Y-%m-%d')
    return df.to_dict(orient="records")

@app.get("/api/summary/{country}")
@lru_cache(maxsize=128)
def get_summary(country: str):
    """Returns key metrics for a country."""
    conn = get_snowflake_connection()
    query = "SELECT DATE, CASE_TYPE, CASES FROM JHU_COVID_19 WHERE COUNTRY_REGION = %(country)s"
    df = pd.read_sql(query, conn, params={'country': country})
    if df.empty:
        return {"total_cases": 0, "total_deaths": 0, "mortality_rate": 0}

    total_cases = df[df['CASE_TYPE'] == 'Confirmed']['CASES'].max()
    total_deaths = df[df['CASE_TYPE'] == 'Deaths']['CASES'].max()
    mortality_rate = (total_deaths / total_cases * 100) if total_cases > 0 else 0
    
    return {
        "total_cases": int(total_cases),
        "total_deaths": int(total_deaths),
        "mortality_rate": round(mortality_rate, 2)
    }

@app.get("/api/forecast/{country}")
@lru_cache(maxsize=32)
def get_forecast(country: str):
    """Generates a 90-day forecast. More robust error handling."""
    try:
        historical_data = get_country_timeseries(country)
        df = pd.DataFrame(historical_data)
        df_confirmed = df[df['CASE_TYPE'] == 'Confirmed'][['DATE', 'CASES']]

        if len(df_confirmed) < 30: 
            raise HTTPException(status_code=400, detail="Not enough data points to make a forecast.")

        df_prophet = df_confirmed.rename(columns={'DATE': 'ds', 'CASES': 'y'})
        df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])

        model = Prophet(daily_seasonality=True)
        model.fit(df_prophet)
        future = model.make_future_dataframe(periods=90)
        forecast = model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient="records")
    except Exception as e:
        print(f"Forecast error for {country}: {e}")
        return []

@app.get("/api/comments/{country}")
def get_comments(country: str):
    return {"comments": list(comments_collection.find({'country': country}, {'_id': 0}))}

@app.post("/api/comments", status_code=201)
def add_comment(comment: Comment):
    comment_data = {'country': comment.country, 'comment': comment.comment, 'created_at': datetime.now(timezone.utc)}
    result = comments_collection.insert_one(comment_data)
    return {"status": "success", "comment_id": str(result.inserted_id)}
@app.get("/api/peak-weeks")
@lru_cache(maxsize=1) 
def get_peak_weeks():
    """
    Finds the single week with the most new cases for each country.
    """
    try:
        conn = get_snowflake_connection()
        query = """
            WITH daily_cases AS (
                SELECT
                    COUNTRY_REGION,
                    DATE,
                    CASES - LAG(CASES, 1, 0) OVER (PARTITION BY COUNTRY_REGION, CASE_TYPE ORDER BY DATE) AS NEW_CASES
                FROM JHU_COVID_19
                WHERE CASE_TYPE = 'Confirmed' AND PROVINCE_STATE IS NULL
            ),
            weekly_cases AS (
                SELECT
                    COUNTRY_REGION,
                    DATE_TRUNC('week', DATE) AS week_start_date,
                    SUM(NEW_CASES) AS total_weekly_cases
                FROM daily_cases
                GROUP BY COUNTRY_REGION, week_start_date
            ),
            ranked_weeks AS (
                SELECT
                    COUNTRY_REGION,
                    week_start_date,
                    total_weekly_cases,
                    ROW_NUMBER() OVER (PARTITION BY COUNTRY_REGION ORDER BY total_weekly_cases DESC) as week_rank
                FROM weekly_cases
            )
            SELECT
                COUNTRY_REGION,
                week_start_date,
                CAST(total_weekly_cases AS INT) AS peak_weekly_cases
            FROM ranked_weeks
            WHERE week_rank = 1
            ORDER BY peak_weekly_cases DESC
            LIMIT 20; -- Limit to the top 20 for a clean chart
        """
        df = pd.read_sql(query, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))