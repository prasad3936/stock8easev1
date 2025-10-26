from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

def fetch_data():
    try:
        response = requests.get("http://localhost:5000/billing/billing-data")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
    return []

def parse_date(timestamp):
    try:
        return datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S GMT")
    except Exception as e:
        print(f"Failed to parse timestamp: {timestamp}, error: {e}")
        return None

def group_sales_by_month(data):
    sales_by_month = defaultdict(lambda: defaultdict(int))
    sales_all = defaultdict(int)
    for record in data:
        timestamp = record.get("timestamp")
        date = parse_date(timestamp)
        if date:
            year_month = date.strftime("%Y-%m")
            key = (record["product_code"], record["product_name"])
            quantity = record.get("quantity", 0)
            sales_by_month[year_month][key] += quantity
            sales_all[key] += quantity
    return sales_by_month, sales_all

def get_top_least_products(sales_dict):
    if not sales_dict:
        return None, None
    sorted_items = sorted(sales_dict.items(), key=lambda x: x[1], reverse=True)
    top = sorted_items[0]
    least = sorted_items[-1]
    return top, least

def filter_sales_by_month_range(sales_by_month, months):
    current_month = datetime.now().replace(day=1)
    result = defaultdict(int)
    for i in range(months):
        month_key = (current_month - timedelta(days=30 * i)).strftime("%Y-%m")
        for k, v in sales_by_month.get(month_key, {}).items():
            result[k] += v
    return result

@app.route('/predict', methods=['GET'])
def predict():
    data = fetch_data()
    sales_by_month, _ = group_sales_by_month(data)
    today = datetime.now()
    today_key = today.strftime("%Y-%m")
    today_day = today.day

    # Sales for today
    day_sales = defaultdict(int)
    for record in data:
        date = parse_date(record.get("timestamp", ""))
        if date and date.date() == today.date():
            key = (record["product_code"], record["product_name"])
            day_sales[key] += record.get("quantity", 0)

    predictions = {}

    def safe_wrap(sales):
        top, least = get_top_least_products(sales)
        return {
            "most_sold": {
                "product_code": top[0][0],
                "product_name": top[0][1],
                "total_quantity": top[1]
            } if top else {},
            "least_sold": {
                "product_code": least[0][0],
                "product_name": least[0][1],
                "total_quantity": least[1]
            } if least else {}
        }

    predictions['today'] = safe_wrap(day_sales)
    predictions['this_month'] = safe_wrap(sales_by_month.get(today_key, {}))
    predictions['last_3_months'] = safe_wrap(filter_sales_by_month_range(sales_by_month, 3))
    predictions['last_6_months'] = safe_wrap(filter_sales_by_month_range(sales_by_month, 6))
    predictions['last_12_months'] = safe_wrap(filter_sales_by_month_range(sales_by_month, 12))

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)
