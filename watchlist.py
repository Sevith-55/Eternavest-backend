from flask import Blueprint, request, jsonify
import yfinance as yf
from datetime import datetime

watchlist_bp = Blueprint('watchlist', __name__)

# In-memory watchlist (use a DB in production)
watchlist = []

@watchlist_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    try:
        updated_watchlist = []
        for stock in watchlist:
            ticker = yf.Ticker(stock['symbol'])
            hist = ticker.history(period='2d')
            if not hist.empty:
                latest_close = float(hist['Close'][-1])
                prev_close = float(hist['Close'][-2]) if len(hist) > 1 else latest_close
                price_change = latest_close - prev_close
                price_change_percent = (price_change / prev_close) * 100 if prev_close != 0 else 0
                
                stock.update({
                    'currentPrice': latest_close,
                    'priceChange': price_change,
                    'priceChangePercent': price_change_percent,
                    'lastUpdated': datetime.now().isoformat()
                })
                updated_watchlist.append(stock)
                
        return jsonify(updated_watchlist)
    except Exception as e:
        return jsonify({'error': f"Failed to fetch watchlist: {str(e)}"}), 500

@watchlist_bp.route('/add-to-watchlist', methods=['POST'])
def add_to_watchlist():
    try:
        data = request.json
        symbol = data.get('symbol')
        price = data.get('price')  # Transaction price
        quantity = data.get('quantity')
        total = data.get('total')
        transaction_type = data.get('type')  # 'buy' or 'sell'
        
        if not symbol or price is None or quantity is None or not transaction_type:
            return jsonify({'error': 'Symbol, price, quantity, and type are required'}), 400

        stock = yf.Ticker(symbol)
        hist = stock.history(period='2d')
        
        if hist.empty:
            return jsonify({'error': 'No data available for this stock'}), 404

        latest_close = float(hist['Close'][-1])
        prev_close = float(hist['Close'][-2]) if len(hist) > 1 else latest_close
        price_change = latest_close - prev_close
        price_change_percent = (price_change / prev_close) * 100 if prev_close != 0 else 0

        # Check if stock already exists in watchlist
        existing_stock = next((s for s in watchlist if s['symbol'] == symbol.upper()), None)
        
        if existing_stock:
            current_quantity = existing_stock['quantity']
            if transaction_type == 'buy':
                new_quantity = current_quantity + quantity
            elif transaction_type == 'sell':
                new_quantity = current_quantity - quantity

            # Update or remove stock based on new quantity
            if new_quantity == 0:
                watchlist.remove(existing_stock)
                return jsonify({'message': f'{symbol} position closed (quantity reached zero)'}), 200
            else:
                existing_stock.update({
                    'price': price,  # Last transaction price
                    'quantity': new_quantity,
                    'total': total,
                    'type': transaction_type,  # Record last transaction type
                    'currentPrice': latest_close,
                    'priceChange': price_change,
                    'priceChangePercent': price_change_percent,
                    'timestamp': datetime.now().isoformat()
                })
                return jsonify(existing_stock), 200
        else:
            # New stock: allow buy (positive) or sell (negative for short)
            new_quantity = quantity if transaction_type == 'buy' else -quantity
            stock_data = {
                'symbol': symbol.upper(),
                'name': stock.info.get('shortName', symbol),
                'price': price,
                'quantity': new_quantity,
                'total': total,
                'type': transaction_type,
                'currentPrice': latest_close,
                'priceChange': price_change,
                'priceChangePercent': price_change_percent,
                'timestamp': datetime.now().isoformat()
            }
            watchlist.append(stock_data)
            return jsonify(stock_data), 201

    except Exception as e:
        return jsonify({'error': f"Failed to add to watchlist: {str(e)}"}), 500

@watchlist_bp.route('/remove-from-watchlist', methods=['DELETE'])
def remove_from_watchlist():
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        global watchlist
        watchlist = [stock for stock in watchlist if stock['symbol'] != symbol.upper()]
        
        return jsonify({'message': 'Stock removed successfully'}), 200

    except Exception as e:
        return jsonify({'error': f"Failed to remove from watchlist: {str(e)}"}), 500