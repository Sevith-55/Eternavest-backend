# news.py
import datetime as dt
import requests
from flask import Blueprint, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load News API key
API_KEY = "a2efa62997c4419d91c5c4f31d76b1fb"


# Create Blueprint
news_blueprint = Blueprint('news', __name__)

def fetch_news_articles(stock_name):
    """Fetch news articles for a given stock."""
    end_date = dt.datetime.today()
    start_date = end_date - dt.timedelta(days=7)

    news_url = f'https://newsapi.org/v2/everything?q={stock_name}&from={start_date}&to={end_date}&sortBy=publishedAt&apiKey={API_KEY}'
    
    try:
        response = requests.get(news_url)
        response.raise_for_status()
        articles = response.json().get('articles', [])[:10]
        logger.debug(f"Fetched {len(articles)} articles for {stock_name}")
        
        formatted_articles = [
            {
                "title": article.get("title", "No title available"),
                "description": article.get("description", "No description available"),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", "")
            }
            for article in articles
        ]
        return formatted_articles
    except requests.RequestException as e:
        logger.error(f"NewsAPI request failed for {stock_name}: {str(e)}")
        return []  # Return empty list on failure

@news_blueprint.route('/news', methods=['GET'])
def get_news():
    ticker = request.args.get('ticker')
    if not ticker:
        logger.warning("No ticker provided in request")
        return jsonify({'error': 'No ticker provided'}), 400
    
    try:
        articles = fetch_news_articles(ticker)
        return jsonify({
            'ticker': ticker,
            'articles': articles
        })
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {str(e)}")
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500