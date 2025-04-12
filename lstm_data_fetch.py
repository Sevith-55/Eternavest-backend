import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sentiment_analysis import get_news_sentiment  # Import sentiment function

def get_stock_data(ticker, start_date, end_date):
    """Fetch stock price data using yfinance"""
    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date, end=end_date)
    return data[["Close"]]

def prepare_data(ticker):
    """Merge stock price data with sentiment scores"""
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=365*5)  # Fetch 5 years of data
    
    stock_data = get_stock_data(ticker, start_date, end_date)
    sentiment_score = get_news_sentiment(ticker)  # Fetch sentiment for last 7 days
    
    stock_data["Sentiment"] = sentiment_score
    stock_data["Sentiment"].fillna(0, inplace=True)  # Handle missing values
    
    # Scale stock prices and sentiment scores
    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(stock_data.values)
    
    return scaled_data, scaler
