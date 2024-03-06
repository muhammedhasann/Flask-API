from flask import Flask, request, jsonify

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


from config import TABLE_NAME 

app = Flask(__name__)

def connect_to_db():
    """Connects to the PostgreSQL database and returns a connection object."""
    try:
        # Use environment variables for secure credential access
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def filter_sort_paginate_data(filters, sort_by, sort_order, page, per_page):
    """
    Fetches data from the database based on filters, sorting, and pagination.
    """
    conn = connect_to_db()
    if not conn:
        return {"message": "Error connecting to database"}, 500

    try:
        # Build query with parameterization for security
        with conn.cursor() as cursor:
            total_count_query = f"""
            SELECT COUNT(*) FROM {TABLE_NAME} {f"WHERE {' AND '.join(f'{key} = %s' for key in filters)}" if filters else ''};
            """
            cursor.execute(total_count_query, list(filters.values()) if filters else [])
            total_count = cursor.fetchone()[0]

            data_query = f"""
            SELECT * FROM {TABLE_NAME}
                {f"WHERE {' AND '.join(f'{key} = %s' for key in filters)}" if filters else ''}
                ORDER BY {sort_by} {sort_order}
                LIMIT {per_page} OFFSET {(page - 1) * per_page};
            """
            cursor.execute(data_query, list(filters.values()) if filters else [])
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

        return {"data": data, "total_count": total_count, "page": page, "per_page": per_page}
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"message": "An error occurred while fetching data"}, 500
    finally:
        conn.close()

@app.route("/assignment/query", methods=["POST"])
def query_data():
    """Handles POST requests containing filtering, sorting, and pagination options."""
    try:
        data = request.get_json()
        filters = data.get("filters", {})
        sort_by = data.get("sort_by", "main_af_vcf")
        sort_order = data.get("sort_order", "desc")
        page = int(data.get("page", 1))  # Ensure page is an integer
        per_page = int(data.get("per_page", 10))  # Ensure per_page is an integer

        # Validate data types before query execution
        if not isinstance(filters, dict):
            return jsonify({"message": "Invalid data types in request body."}), 400

        # ... Add validation for other fields as needed (e.g., sort_by, sort_order)

        # Call function to fetch and process data
        response = filter_sort_paginate_data(filters, sort_by, sort_order, page, per_page)
        return jsonify(response)

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"message": "An error occurred while processing the request."}), 500

if __name__ == "__main__":
    app.run(debug=True)
