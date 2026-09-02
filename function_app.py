import json
import logging
import os

import azure.functions as func
import pyodbc

# NOTE: When deploying, Azure Functions (Python v2 model) expects this file
# to be named function_app.py at the root of the function app project.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Database configuration
DB_SERVER = 'tcp:module08.database.windows.net,1433'
DB_NAME = 'week9-vishal'
DB_USER = 'vishal-admin'
# It is highly recommended to load the password from an environment variable
# (set DB_PASSWORD under Application Settings in the Azure portal)
DB_PASSWORD = os.environ.get('DB_PASSWORD', '_damonSalvatore27V')

# Construct the pyodbc connection string for SQL Authentication
CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server={DB_SERVER};"
    f"Database={DB_NAME};"
    f"Uid={DB_USER};"
    f"Pwd={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

# CORS headers (for production, prefer configuring CORS on the Function App
# itself in the Azure portal under API > CORS)
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def json_response(body: dict, status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body),
        status_code=status_code,
        mimetype="application/json",
        headers=CORS_HEADERS,
    )


@app.route(route="index", methods=["GET"])
def index(req: func.HttpRequest) -> func.HttpResponse:
    html_path = os.path.join(os.path.dirname(__file__), 'week-08.html')
    try:
        with open(html_path, 'r') as f:
            return func.HttpResponse(
                f.read(),
                status_code=200,
                mimetype="text/html",
                headers=CORS_HEADERS,
            )
    except FileNotFoundError:
        return json_response({"error": "week-08.html not found."}, 404)


@app.route(route="login", methods=["GET", "POST", "OPTIONS"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight requests
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    if req.method == "POST":
        username = req.form.get('username')
        password = req.form.get('password')
    else:
        username = req.params.get('username')
        password = req.params.get('password')

    if not username or not password:
        return json_response({"error": "Username and password are required."}, 400)

    conn = None
    try:
        # 1. Connect to the Azure SQL Database
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        # 2. Execute the parameterized query to prevent SQL injection
        query = "SELECT 1 FROM Users WHERE username = ? AND password = ?"
        cursor.execute(query, (username, password))

        # 3. Check if a record was found
        user_exists = cursor.fetchone() is not None

        if user_exists:
            return json_response({"message": "Login Successful", "username": username}, 200)
        else:
            return json_response({"message": "Invalid username or password.", "authenticated": False}, 401)

    except pyodbc.Error as e:
        # Log the error for debugging (visible in Azure's log stream)
        logging.error(f"Database error: {e}")
        return json_response({"error": "A database error occurred."}, 500)
    finally:
        # 4. Always close the connection
        if conn:
            conn.close()
