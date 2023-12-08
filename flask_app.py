from flask import Flask, render_template, jsonify, request
from flask_caching import Cache
import schedule
import time
from flask_paginate import Pagination, get_page_args
from utils import result  # Assuming result() is a function in utils module
# Start the scheduler in a separate thread
import threading
from flask_wtf import FlaskForm
from wtforms import FloatField, BooleanField, SubmitField

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Function to update the cache periodically
def update_cache():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    data = {"timestamp": current_time, "result": result()}
    
    # Retrieve the existing result history from the cache
    result_history = cache.get('result_history') or []
    
    # Append the new result to the history
    result_history.append(data)
    
    # Store the updated result history in the cache
    cache.set('result_history', result_history)
    
    # Store the latest result in the cache
    cache.set('cached_data', data)
    print("Cache updated at", current_time)

# Schedule the cache update every 30 minutes
#schedule.every(30).seconds.do(update_cache)
schedule.every(30).minutes.do(update_cache)

# Start the scheduled task in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

@app.route('/')
def serve_cached_data():
    # Check if mocking is enabled and get mocked values from storage
    mocking_enabled = cache.get('mocking_enabled') or False
    mocked_values = cache.get('mocked_values') or {}

    # Check if mocking is enabled, if so, use mocked values regardless of cache presence
    if mocking_enabled:
        cached_data = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "result": mocked_values}
    else:
        # Check if data is in the cache, if not, fetch and cache it
        cached_data = cache.get('cached_data')
        is_cached = True

        if cached_data is None:
            # Use the actual result if mocking is not enabled
            update_cache()  # Manually trigger cache update to get the latest result
            cached_data = cache.get('cached_data')
            is_cached = False

        cached_data["is_cached"] = is_cached

    return jsonify(cached_data)

@app.route('/refresh-cache')
def refresh_cache():
    # Manually trigger cache update
    update_cache()
    return jsonify({"message": "Cache refreshed"})

@app.route('/result-history', methods=['GET'])
def result_history_page():
    # Retrieve the result history from the cache
    result_history = cache.get('result_history') or []
    
    # Pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(result_history)
    pagination_result_history = result_history[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    
    # Render the result history template with pagination
    return render_template('result_history.html', result_history=pagination_result_history, pagination=pagination)

class MockForm(FlaskForm):
    limit_from_impact = FloatField('Limit from Impact')
    stability_pool_share = FloatField('Stability Pool Share')
    value_at_risk = FloatField('Value at Risk')
    average_parkinson = FloatField('Average Parkinson Volatility')
    latest_ema = FloatField('Latest EMA Volatility')
    enable_mocking = BooleanField('Enable Mocking')
    submit = SubmitField('Submit')

@app.route('/mocking', methods=['GET', 'POST'])
def mocking():
    form = MockForm()

    # Check if mocking is enabled and get mocked values from storage
    mocking_enabled = cache.get('mocking_enabled') or False
    mocked_values = cache.get('mocked_values') or {}

    if form.validate_on_submit():
        # Handle form submission and store values
        mocked_values = {
            "limit_from_impact": form.limit_from_impact.data,
            "stability_pool_share": form.stability_pool_share.data,
            "value_at_risk": form.value_at_risk.data,
            "volatility": {
                "average_parkinson": form.average_parkinson.data,
                "latest_ema": form.latest_ema.data
            }
        }
        mocking_enabled = form.enable_mocking.data

        # Store mocked values and mocking status in the cache
        cache.set('mocking_enabled', mocking_enabled)
        cache.set('mocked_values', mocked_values)

    return render_template('mocking.html', form=form, mocking_enabled=mocking_enabled, mocked_values=mocked_values)
