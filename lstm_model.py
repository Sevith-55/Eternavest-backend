import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM
from lstm_data_fetch import prepare_data  # Import from lstm_data_fetch.py

def train_lstm(scaled_data):
    """Build and train an LSTM model"""
    X_train, y_train = [], []
    prediction_days = 60

    for i in range(prediction_days, len(scaled_data)):
        X_train.append(scaled_data[i-prediction_days:i])
        y_train.append(scaled_data[i, 0])  # Predicting the stock price

    X_train, y_train = np.array(X_train), np.array(y_train)
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 2))  # 2 features (Close & Sentiment)

    # Build LSTM model
    model = Sequential([
        LSTM(units=100, return_sequences=True, input_shape=(X_train.shape[1], 2)),
        Dropout(0.2),
        LSTM(units=100, return_sequences=True),
        Dropout(0.2),
        LSTM(units=100),
        Dropout(0.2),
        Dense(units=1)  # Output: predicted stock price
    ])

    model.compile(optimizer="adam", loss="mean_squared_error")
    model.fit(X_train, y_train, epochs=25, batch_size=32)

    return model

# Standalone test
if __name__ == "__main__":
    ticker = ""
    scaled_data, scaler = prepare_data(ticker)
    model = train_lstm(scaled_data)
    # Test prediction
    test_data = scaled_data[-60:]
    test_data = np.reshape(test_data, (1, 60, 2))
    pred = model.predict(test_data)
    dummy_input = np.array([[pred[0][0], 0]])  # Only Close and Sentiment
    pred_price = scaler.inverse_transform(dummy_input)[0][0]
    print(f"Predicted price for {ticker}: {pred_price:.2f}")