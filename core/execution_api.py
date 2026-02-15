"""
Execution API Endpoints
Order execution and position management endpoints.
"""
from flask import Blueprint, request, jsonify
from loguru import logger
from typing import Dict, List, Any
from datetime import datetime
import asyncio
import json

execution_api = Blueprint('execution_api', __name__, url_prefix='/api/execution')


def get_execution_engine():
    """Get execution engine instance."""
    from core.live_execution_engine import get_execution_engine, ExecutionConfig, ExecutionMode
    return get_execution_engine()


@execution_api.route('/status', methods=['GET'])
def get_status():
    """Get execution engine status."""
    engine = get_execution_engine()
    return jsonify({
        'success': True,
        'status': engine.get_status()
    })


@execution_api.route('/mode', methods=['POST'])
def set_mode():
    """Set execution mode."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'paper')
        
        from core.live_execution_engine import ExecutionMode
        engine = get_execution_engine()
        engine.set_execution_mode(ExecutionMode(mode))
        
        return jsonify({
            'success': True,
            'mode': mode,
            'message': f'Execution mode set to {mode}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/order', methods=['POST'])
def execute_order():
    """Execute an order."""
    try:
        data = request.get_json()
        
        engine = get_execution_engine()
        
        # Run async execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(engine.execute_order(
            symbol=data.get('symbol'),
            side=data.get('side'),
            order_type=data.get('order_type', 'market'),
            quantity=float(data.get('quantity', 0)),
            price=float(data.get('price')) if data.get('price') else None,
            exchange=data.get('exchange'),
            account_id=data.get('account_id', 'default'),
            stop_loss=float(data.get('stop_loss')) if data.get('stop_loss') else None,
            take_profit=float(data.get('take_profit')) if data.get('take_profit') else None,
            leverage=int(data.get('leverage', 1)),
            reduce_only=data.get('reduce_only', False),
            post_only=data.get('post_only', False),
            time_in_force=data.get('time_in_force', 'GTC')
        ))
        loop.close()
        
        return jsonify({
            'success': result.success,
            'order_id': result.order_id,
            'status': result.status.value,
            'filled_quantity': result.filled_quantity,
            'average_price': result.average_price,
            'fee': result.fee,
            'slippage': result.slippage,
            'latency_ms': result.latency_ms,
            'retry_count': result.retry_count,
            'error': result.error_message
        })
        
    except Exception as e:
        logger.error(f"Order execution error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/order/<order_id>', methods=['DELETE'])
def cancel_order(order_id: str):
    """Cancel an order."""
    try:
        symbol = request.args.get('symbol', '')
        exchange = request.args.get('exchange')
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            engine.cancel_order(order_id, symbol, exchange)
        )
        loop.close()
        
        return jsonify({
            'success': success,
            'order_id': order_id,
            'message': 'Order cancelled' if success else 'Failed to cancel order'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/orders/cancel-all', methods=['POST'])
def cancel_all_orders():
    """Cancel all open orders."""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        exchange = data.get('exchange')
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        cancelled = loop.run_until_complete(
            engine.cancel_all_orders(symbol, exchange)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'cancelled': cancelled,
            'message': f'{cancelled} orders cancelled'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/orders/open', methods=['GET'])
def get_open_orders():
    """Get open orders."""
    try:
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange')
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        orders = loop.run_until_complete(
            engine.get_open_orders(symbol, exchange)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'orders': orders,
            'count': len(orders)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/positions', methods=['GET'])
def get_positions():
    """Get current positions."""
    try:
        exchange = request.args.get('exchange')
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        positions = loop.run_until_complete(engine.get_positions(exchange))
        loop.close()
        
        return jsonify({
            'success': True,
            'positions': positions,
            'count': len(positions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/positions/<symbol>/close', methods=['POST'])
def close_position(symbol: str):
    """Close a position."""
    try:
        data = request.get_json() or {}
        exchange = data.get('exchange')
        quantity = float(data.get('quantity')) if data.get('quantity') else None
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            engine.close_position(symbol, exchange, quantity)
        )
        loop.close()
        
        return jsonify({
            'success': result.success,
            'order_id': result.order_id,
            'filled_quantity': result.filled_quantity,
            'average_price': result.average_price,
            'error': result.error_message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/positions/close-all', methods=['POST'])
def close_all_positions():
    """Close all positions."""
    try:
        data = request.get_json() or {}
        exchange = data.get('exchange')
        
        engine = get_execution_engine()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        closed = loop.run_until_complete(engine.close_all_positions(exchange))
        loop.close()
        
        return jsonify({
            'success': True,
            'closed': closed,
            'message': f'{closed} positions closed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/history', methods=['GET'])
def get_execution_history():
    """Get execution history."""
    limit = int(request.args.get('limit', 50))
    
    engine = get_execution_engine()
    history = engine.get_execution_history(limit)
    
    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


# Paper Trading Endpoints

@execution_api.route('/paper/balance', methods=['GET'])
def get_paper_balance():
    """Get paper trading balance."""
    engine = get_execution_engine()
    return jsonify({
        'success': True,
        'balance': engine.get_paper_balance()
    })


@execution_api.route('/paper/balance', methods=['POST'])
def set_paper_balance():
    """Set paper trading balance."""
    try:
        data = request.get_json()
        balance = float(data.get('balance', 100000))
        
        engine = get_execution_engine()
        engine.set_paper_balance(balance)
        
        return jsonify({
            'success': True,
            'balance': balance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@execution_api.route('/paper/trades', methods=['GET'])
def get_paper_trades():
    """Get paper trading history."""
    limit = int(request.args.get('limit', 50))
    
    engine = get_execution_engine()
    trades = engine.get_paper_trades(limit)
    
    return jsonify({
        'success': True,
        'trades': trades,
        'count': len(trades)
    })


@execution_api.route('/paper/reset', methods=['POST'])
def reset_paper_trading():
    """Reset paper trading."""
    try:
        data = request.get_json() or {}
        balance = float(data.get('balance', 100000))
        
        engine = get_execution_engine()
        engine.reset_paper_trading(balance)
        
        return jsonify({
            'success': True,
            'balance': balance,
            'message': 'Paper trading reset'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def register_execution_routes(app):
    """Register execution API routes with Flask app."""
    app.register_blueprint(execution_api)
    logger.info("Execution API routes registered")
