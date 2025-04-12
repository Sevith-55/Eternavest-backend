from flask import Flask
from flask_cors import CORS
from search import search_blueprint
from stock_data import stock_data_blueprint
from watchlist import watchlist_bp
from sentiment_analysis import sentiment_blueprint
from news import news_blueprint

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Register blueprints with /api prefix
app.register_blueprint(search_blueprint, url_prefix='/api')
app.register_blueprint(stock_data_blueprint, url_prefix='/api')
app.register_blueprint(watchlist_bp, url_prefix='/api')
app.register_blueprint(sentiment_blueprint, url_prefix='/api')
app.register_blueprint(news_blueprint, url_prefix='/api')

@app.route('/')
def home():
    return "Flask API is running!"

if __name__ == "__main__":
    app.run(port=5000)