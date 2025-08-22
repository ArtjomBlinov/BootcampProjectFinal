# COVID-19 Data Integration, Analysis, and Visualization Platform

This project is an integrated data analytics and visualization platform that offers insights into the spread and patterns of the COVID-19 virus. It leverages a COVID-19 dataset from the Snowflake Marketplace, combines it with supplementary data, and presents the findings in an interactive web dashboard.

## Features 
* **Interactive Dashboard:** A web-based dashboard built with Dash and Plotly for dynamic data exploration.
* **Data Integration:** Combines structured data from Snowflake with user-generated annotations stored in MongoDB.
* **Advanced Analytics:** Includes features like time-series forecasting to predict future case trends and K-Means clustering to identify country groups with similar pandemic impacts.
* **Pattern Recognition:** Utilizes SQL to identify patterns like the "peak infection week" for each country.
* **RESTful API:** A backend built with FastAPI serves all data to the frontend, ensuring a clean and scalable architecture.

## Architecture 
The platform consists of three main components:
1.  **Data Layer:** Snowflake for the primary COVID-19 dataset and MongoDB for storing user comments.
2.  **Backend Layer:** A Python FastAPI server that handles all data querying, processing, and analytical calculations.
3.  **Frontend Layer:** A Dash and Plotly dashboard that communicates with the API to visualize data.



## Prerequisites
* Python 3.9+

---
## Setup and Installation 
To set up the project locally, navigate to the main project folder in your terminal and follow these steps:

**1. Create and Activate a Virtual Environment**
A virtual environment keeps your project's dependencies separate from other Python projects.

cd ~/Downloads/BootcampProjectFinal-main

* **Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
* **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

**2. Install Dependencies**
Install all the required Python libraries using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

**3. Configure Environment Variables**
Create a file named `.env` inside the `app` subfolder. This file will store your database credentials.

Copy the following content into the `.env` file and replace the placeholders with your actual credentials:
```env
# app/.env file
SNOWFLAKE_USER="your_snowflake_user"
SNOWFLAKE_PASSWORD="your_snowflake_password"
SNOWFLAKE_ACCOUNT="your_snowflake_account_identifier"
SNOWFLAKE_WAREHOUSE="COVID_WH"
SNOWFLAKE_DATABASE="COVID19_EPIDEMIOLOGICAL_DATA"
MONGO_URI="your_mongodb_connection_string"
```

---
## Running the Application 
You need to run the backend API and the frontend dashboard in two separate terminals.

**1. Start the Backend API**
In your first terminal (from the project's root directory), run:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

**2. Start the Frontend Dashboard**
In a second terminal (from the project's root directory), run:
```bash
python app/dash_app.py
```
The dashboard will be available at `http://127.0.0.1:8050`.


Open **`http://127.0.0.1:8050`** in your web browser to use the application.
