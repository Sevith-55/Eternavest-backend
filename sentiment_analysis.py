import datetime as dt
import requests
from transformers import pipeline
from flask import Blueprint, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize sentiment analysis pipeline
pipe = pipeline("text-classification", model="ProsusAI/finbert")

# Load News API key (ensure News_API.txt is in the same directory or adjust the path)
API_KEY = open("News_API.txt").read().strip()

# Create Blueprint
sentiment_blueprint = Blueprint('sentiment', __name__)

def get_news_sentiment(stock_name):
    """Fetch and analyze sentiment from news articles for a stock."""
    end_date = dt.datetime.today()
    start_date = end_date - dt.timedelta(days=7)

    news_url = f'https://newsapi.org/v2/everything?q={stock_name}&from={start_date}&to={end_date}&sortBy=popularity&apiKey={API_KEY}'
    
    try:
        response = requests.get(news_url)
        response.raise_for_status()
        articles = response.json().get('articles', [])[:10]
        logger.debug(f"Fetched {len(articles)} articles for {stock_name}")
    except requests.RequestException as e:
        logger.error(f"NewsAPI request failed for {stock_name}: {str(e)}")
        return 0  # Default to neutral on fetch failure

    if not articles:
        logger.warning(f"No articles found for {stock_name}")
        return 0

    sentiment_scores = []
    for article in articles:
        description = article.get("description", "")
        if description and isinstance(description, str):
            try:
                sentiment_result = pipe(description)[0]
                sentiment_label = sentiment_result["label"]
                sentiment_score = sentiment_result["score"]
                if sentiment_label == "positive":
                    sentiment_scores.append(sentiment_score)
                elif sentiment_label == "negative":
                    sentiment_scores.append(-sentiment_score)
                else:  # neutral
                    sentiment_scores.append(0)
            except Exception as e:
                logger.error(f"Sentiment analysis failed for {stock_name} article: {str(e)}")
                sentiment_scores.append(0)
        else:
            logger.debug(f"Empty or invalid description for {stock_name}")
            sentiment_scores.append(0)

    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    logger.debug(f"Average sentiment for {stock_name}: {avg_sentiment}")
    return avg_sentiment

@sentiment_blueprint.route('/sentiment', methods=['GET'])
def sentiment():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    
    try:
        sentiment_score = get_news_sentiment(ticker)
        # Normalize to 0-100 scale (assuming get_news_sentiment returns -1 to 1)
        normalized_score = int((sentiment_score + 1) * 50)  # Map -1..1 to 0..100
        label = 'Neutral'
        if normalized_score <= 20:
            label = 'Strong Sell'
        elif normalized_score <= 40:
            label = 'Sell'
        elif normalized_score <= 60:
            label = 'Neutral'
        elif normalized_score <= 80:
            label = 'Buy'
        else:
            label = 'Strong Buy'
        
        return jsonify({
            'ticker': ticker,
            'score': normalized_score,
            'label': label
        })
    except Exception as e:
        logger.error(f"Error processing sentiment for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500