from flask import Blueprint, request, jsonify
import yfinance as yf
from yfinance.search import Search
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

search_blueprint = Blueprint("search", __name__)

@search_blueprint.route("/search", methods=["GET"])
def search_stock():
    try:
        query = request.args.get("query", '').strip().upper()
        if not query or len(query) < 1:
            return jsonify({"quotes": [], "message": "Query too short"}), 200

        # Use yfinance Search class
        search = Search(
            query=query,
            max_results=15,  # Fetch more for better filtering
            news_count=5,    # Fetch up to 5 related news articles
            lists_count=5,   # Include related lists
            include_cb=True,
            include_nav_links=True,
            include_research=True,
            include_cultural_assets=True,
            enable_fuzzy_query=True,
            recommended=10,
            timeout=10
        )

        # Get quotes from search results
        quotes = search.quotes
        logger.debug(f"Raw quotes for {query}: {quotes}")

        # Include all major markets: Stocks, Crypto, Futures, Options, ETFs, Indices
        valid_types = {'EQUITY', 'CRYPTOCURRENCY', 'FUTURE', 'OPTION', 'ETF', 'INDEX'}
        valid_exchanges = {
            'NMS', 'NYQ', 'NSI', 'BSE', 'CCC', 'CME', 'NYM', 'CBT', 'CMX',  # Stocks & Futures
            'NSE', 'BSE', 'TSX', 'LSE', 'ASX', 'HKEX', 'SGX',               # International Stocks
            'OTC', 'AMEX', 'EUREX', 'EURONEXT', 'NASDAQ', 'NYSE', 'CBOE',   # Options & ETFs
            'BINANCE', 'COINBASE', 'KRAKEN', 'HUOBI', 'FTX', 'BITSTAMP'     # Crypto
        }

        # Filter results
        filtered_quotes = [
            {
                'symbol': quote.get('symbol', ''),
                'shortname': quote.get('shortname', ''),
                'exchange': quote.get('exchange', ''),
                'type': quote.get('quoteType', ''),
                'price': quote.get('price', 0),
                'change': quote.get('change', 0)
            }
            for quote in quotes
            if quote.get('quoteType') in valid_types and quote.get('exchange') in valid_exchanges
        ]

        # Ensure at least 10 results (or all available if fewer)
        results = filtered_quotes[:max(10, len(filtered_quotes))]
        logger.debug(f"Filtered results for {query}: {results}")

        # Fetch related news articles
        news = search.news if hasattr(search, 'news') else []
        formatted_news = [
            {
                'title': article.get('title', ''),
                'publisher': article.get('publisher', ''),
                'link': article.get('link', ''),
                'summary': article.get('summary', '')
            }
            for article in news
        ]

        return jsonify({
            "quotes": results,
            "news": formatted_news,
            "count": len(results),
            "message": "No matching stocks found" if not results else "Success"
        }), 200

    except Exception as e:
        logger.error(f"Search endpoint error: {str(e)}")
        return jsonify({
            "error": "Search failed",
            "message": str(e),
            "quotes": [],
            "news": []
        }), 500

@search_blueprint.route("/clear-cache", methods=["POST"])
def clear_search_cache():
    # Note: Search class uses internal caching via YfData; no direct cache_clear here
    return jsonify({"message": "Cache clearing not supported for Search class"}), 200
