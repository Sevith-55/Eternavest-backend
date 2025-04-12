from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import numpy as np
import yfinance as yf
import pandas as pd
from datetime import datetime

from lstm_data_fetch import prepare_data
from lstm_model import train_lstm

app = Flask(__name__)
CORS(app)

stock_data_blueprint = Blueprint("stock_data", __name__)

def calculate_support_resistance(history, window=20):
    """Calculate support and resistance levels from historical data."""
    # Use a rolling window to find local highs (resistance) and lows (support)
    history['Resistance'] = history['High'].rolling(window=window, center=True).max()
    history['Support'] = history['Low'].rolling(window=window, center=True).min()

    # Get the most recent valid support and resistance levels
    recent_resistance = history['Resistance'].dropna().iloc[-1]
    recent_support = history['Support'].dropna().iloc[-1]

    return recent_support, recent_resistance

def get_sentiment_score(ticker):
    """Mock sentiment analysis (replace with real API like NewsAPI or Twitter)."""
    # For now, return a dummy sentiment score between -1 (bearish) and 1 (bullish)
    # In practice, you'd fetch news headlines or tweets and analyze them
    import random
    sentiment = random.uniform(-1, 1)  # Placeholder
    return sentiment

def calculate_trade_levels(current_price, support, resistance, sentiment_score):
    """Calculate Buy, Sell, and Stop Loss based on market structure and sentiment."""
    # Base buy/sell levels on support/resistance
    suggested_buy_price = support * 1.01  # Buy slightly above support (1% buffer)
    suggested_sell_price = resistance * 0.99  # Sell slightly below resistance (1% buffer)

    # Adjust based on sentiment
    sentiment_adjustment = 0.02 * sentiment_score  # 2% adjustment per sentiment point
    suggested_buy_price *= (1 + sentiment_adjustment)
    suggested_sell_price *= (1 + sentiment_adjustment)

    # Stop loss logic:
    # - For buying: below support
    # - For selling: above resistance
    stop_loss = (
        support * 0.98 if current_price > support  # 2% below support for buy
        else resistance * 1.02  # 2% above resistance for sell
    )

    # Ensure levels make sense relative to current price
    if suggested_buy_price >= current_price:
        suggested_buy_price = None  # No buy signal if above current price
    if suggested_sell_price <= current_price:
        suggested_sell_price = None  # No sell signal if below current price

    return suggested_buy_price, suggested_sell_price, stop_loss

@stock_data_blueprint.route("/get-data", methods=["GET"])
def get_stock_data():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    try:
        stock = yf.Ticker(symbol)
        history = stock.history(period="max")

        if history.empty:
            return jsonify({"error": f"No data found for symbol {symbol}"}), 404

        history.reset_index(inplace=True)
        history["Date"] = history["Date"].astype(str)

        formatted_data = [
            {
                "time": int(pd.Timestamp(row["Date"]).timestamp()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
            }
            for _, row in history.iterrows()
        ]

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": f"Failed to fetch stock data: {str(e)}"}), 500

@stock_data_blueprint.route("/predict", methods=["GET"])
def get_lstm_data():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Ticker symbol is required"}), 400

    try:
        # Fetch historical data
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")  # Use 1 year for support/resistance
        if history.empty:
            return jsonify({"error": f"No data found for ticker {ticker}"}), 404

        current_price = float(history["Close"].iloc[-1])

        # Calculate support and resistance
        support, resistance = calculate_support_resistance(history)

        # Fetch and prepare 5-year data for LSTM (if still needed)
        scaled_data, scaler = prepare_data(ticker)
        if len(scaled_data) < 60:
            return jsonify({"error": "Not enough data for prediction (need 60 days)"}), 400

        # Train LSTM model
        model = train_lstm(scaled_data)

        # Predict next day's stock price
        test_data = scaled_data[-60:]
        test_data = np.reshape(test_data, (1, 60, 2))  # 2 features
        prediction = model.predict(test_data)
        dummy_input = np.array([[prediction[0][0], 0]])
        predicted_price = scaler.inverse_transform(dummy_input)[0][0]

        # Get sentiment score (mock for now)
        sentiment_score = get_sentiment_score(ticker)

        # Calculate trade levels based on market structure and sentiment
        buy_price, sell_price, stop_loss = calculate_trade_levels(
            current_price, support, resistance, sentiment_score
        )

        return jsonify({
            "stock": ticker,
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),  # Still included for reference
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "sentiment_score": round(sentiment_score, 2),
            "suggested_buy_price": round(buy_price, 2) if buy_price else None,
            "suggested_sell_price": round(sell_price, 2) if sell_price else None,
            "suggested_stop_loss": round(stop_loss, 2)
        })

    except Exception as e:
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500

app.register_blueprint(stock_data_blueprint)

if __name__ == "__main__":
    app.run(port=5000, debug=True)