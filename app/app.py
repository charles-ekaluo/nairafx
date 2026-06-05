"""
NairaFX - Nigerian Naira Exchange Rate Tracker

A simple web application that displays current exchange rates for the
Nigerian Naira against major international currencies. The app fetches
live rates from a public exchange rate API, caches them in memory to
avoid hammering the API on every page load, and displays them in a
clean web interface.

This service simulates the kind of FX rate display that banks and
fintechs in Nigeria need to show on their dashboards.
"""

from flask import Flask, render_template_string
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------------------------------------------------------------------
# Configuration
# All configuration is read from environment variables so the same
# image can be deployed to different environments (local, dev, prod)
# without rebuilding. This follows 12-factor app principles.
# ---------------------------------------------------------------------
APP_NAME = os.getenv('APP_NAME', 'NairaFX')
REFRESH_MINUTES = int(os.getenv('REFRESH_MINUTES', '15'))

# ---------------------------------------------------------------------
# In-memory cache
# This dictionary holds the most recently fetched rates and the time
# they were fetched. We cache to avoid calling the external API on
# every single page load — which would be slow and could hit rate limits.
# ---------------------------------------------------------------------
cache = {
    'rates': None,
    'last_updated': None
}

# ---------------------------------------------------------------------
# Fallback rates
# If the external API is unreachable, we fall back to these hardcoded
# values rather than showing the user a broken page. Banks always
# want graceful degradation in customer-facing systems.
# ---------------------------------------------------------------------
FALLBACK_RATES = {
    'USD': 1530.50,
    'GBP': 1925.75,
    'EUR': 1655.30,
    'CAD': 1115.20,
    'CNY': 215.40
}


def fetch_rates():
    """
    Fetch the latest exchange rates from a free public API.

    Uses open.er-api.com which doesn't require an API key for basic usage.
    If the API call fails for any reason, returns hardcoded fallback rates
    so the application keeps working even when the upstream service is down.
    """
    try:
        # The API returns rates with USD as the base currency
        response = requests.get(
            'https://open.er-api.com/v6/latest/USD',
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            # NGN per 1 USD (e.g. 1530.50)
            ngn_per_usd = data['rates'].get('NGN', 0)

            if ngn_per_usd > 0:
                rates = {}

                # Calculate how many Naira equals 1 unit of each currency
                # For USD it's the rate directly; for others we cross-rate via USD
                for currency in ['USD', 'GBP', 'EUR', 'CAD', 'CNY']:
                    if currency == 'USD':
                        rates[currency] = ngn_per_usd
                    else:
                        # If 1 USD = X NGN, and 1 USD = Y of other currency,
                        # then 1 unit of other currency = X/Y NGN
                        units_per_usd = data['rates'].get(currency, 1)
                        rates[currency] = ngn_per_usd / units_per_usd

                return rates
    except Exception as e:
        # In a production system you would log this to Azure Monitor
        # so the ops team gets alerted when the upstream API is failing
        print(f"Error fetching rates from API: {e}")

    # Return fallback rates if anything went wrong
    return FALLBACK_RATES


def get_rates():
    """
    Returns the current rates, refreshing from the API if the cache is stale.

    This is a simple time-based cache: if the rates were fetched within
    the last REFRESH_MINUTES, we return the cached value. Otherwise we
    fetch fresh rates from the API.
    """
    now = datetime.now()

    cache_is_empty = cache['rates'] is None or cache['last_updated'] is None
    cache_is_stale = (
        not cache_is_empty and
        now - cache['last_updated'] > timedelta(minutes=REFRESH_MINUTES)
    )

    if cache_is_empty or cache_is_stale:
        cache['rates'] = fetch_rates()
        cache['last_updated'] = now

    return cache['rates'], cache['last_updated']


@app.route('/')
def home():
    """
    Main page — displays the current exchange rates in a clean table.
    """
    rates, last_updated = get_rates()

    # The HTML template is defined inline for simplicity
    # In a larger app this would live in a separate templates/ folder
    html = '''
    <html>
    <head>
        <title>NairaFX - Exchange Rate Tracker</title>
        <style>
            body {
                font-family: -apple-system, Arial, sans-serif;
                max-width: 700px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            h1 { color: #006633; margin-top: 0; }
            .subtitle { color: #666; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; }
            th, td {
                padding: 16px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            th {
                background: #f9f9f9;
                font-weight: 600;
                color: #333;
            }
            .rate {
                font-weight: 600;
                color: #006633;
                font-size: 18px;
            }
            .currency { font-weight: 500; }
            .footer {
                margin-top: 30px;
                color: #888;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{ app_name }}</h1>
            <p class="subtitle">Live exchange rates for the Nigerian Naira</p>
            <table>
                <tr><th>Currency</th><th>Rate (1 unit = NGN)</th></tr>
                {% for currency, rate in rates.items() %}
                <tr>
                    <td class="currency">{{ currency }}</td>
                    <td class="rate">&#8358;{{ "{:,.2f}".format(rate) }}</td>
                </tr>
                {% endfor %}
            </table>
            <div class="footer">
                Last updated: {{ last_updated.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                Rates refresh every {{ refresh_minutes }} minutes
            </div>
        </div>
    </body>
    </html>
    '''

    return render_template_string(
        html,
        app_name=APP_NAME,
        rates=rates,
        last_updated=last_updated,
        refresh_minutes=REFRESH_MINUTES
    )


@app.route('/health')
def health():
    """
    Health check endpoint. Cloud load balancers and monitoring systems
    call this to verify the application is running. Returns HTTP 200
    with a small JSON payload.
    """
    return {'status': 'healthy', 'app': APP_NAME}, 200


if __name__ == '__main__':
    # Bind to 0.0.0.0 so the container is reachable from outside
    # (binding to localhost only would make it unreachable from the host)
    app.run(host='0.0.0.0', port=5000)
