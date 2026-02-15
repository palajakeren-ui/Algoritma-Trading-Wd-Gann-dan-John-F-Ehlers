"""
Trading System API Endpoints
Orchestrator, Journal, and Reports API.
"""
from flask import Blueprint, request, jsonify, send_file
from loguru import logger
from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import io

trading_api = Blueprint('trading_api', __name__, url_prefix='/api/trading')


# ========================
# Orchestrator Endpoints
# ========================

@trading_api.route('/orchestrator/status', methods=['GET'])
def get_orchestrator_status():
    """Get orchestrator status."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        return jsonify({
            'success': True,
            'status': orchestrator.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'status': {
                'state': 'stopped',
                'symbols': [],
                'session': None
            }
        })


@trading_api.route('/orchestrator/start', methods=['POST'])
def start_orchestrator():
    """Start trading orchestrator."""
    try:
        data = request.get_json() or {}
        
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator({
            'symbols': data.get('symbols', []),
            'timeframes': data.get('timeframes', ['1h']),
            'scan_interval': data.get('scan_interval', 60)
        })
        
        # Configure symbols
        for symbol in data.get('symbols', []):
            orchestrator.add_symbol(symbol)
        
        # Start async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(orchestrator.start())
        loop.close()
        
        return jsonify({
            'success': success,
            'message': 'Orchestrator started' if success else 'Failed to start',
            'status': orchestrator.get_status()
        })
        
    except Exception as e:
        logger.error(f"Orchestrator start error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/stop', methods=['POST'])
def stop_orchestrator():
    """Stop trading orchestrator."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(orchestrator.stop())
        loop.close()
        
        return jsonify({
            'success': True,
            'message': 'Orchestrator stopped'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/pause', methods=['POST'])
def pause_orchestrator():
    """Pause trading."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        orchestrator.pause()
        
        return jsonify({
            'success': True,
            'message': 'Trading paused'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/resume', methods=['POST'])
def resume_orchestrator():
    """Resume trading."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        orchestrator.resume()
        
        return jsonify({
            'success': True,
            'message': 'Trading resumed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/symbols', methods=['POST'])
def add_symbol():
    """Add symbol to watch list."""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol required'
            }), 400
        
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        orchestrator.add_symbol(symbol)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'message': f'Symbol {symbol} added'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/symbols/<symbol>', methods=['DELETE'])
def remove_symbol(symbol: str):
    """Remove symbol from watch list."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        orchestrator.remove_symbol(symbol)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'message': f'Symbol {symbol} removed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/orchestrator/sessions', methods=['GET'])
def get_sessions():
    """Get session history."""
    try:
        from core.trading_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        return jsonify({
            'success': True,
            'sessions': orchestrator.get_session_history()
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'sessions': []
        })


# ========================
# Journal Endpoints
# ========================

@trading_api.route('/journal/trades', methods=['GET'])
def get_journal_trades():
    """Get journal trades."""
    try:
        status = request.args.get('status', 'closed')  # open, closed, all
        limit = int(request.args.get('limit', 100))
        symbol = request.args.get('symbol')
        
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        if status == 'open':
            trades = journal.get_open_trades()
        elif status == 'closed':
            trades = journal.get_closed_trades(limit)
        else:
            trades = journal.get_open_trades() + journal.get_closed_trades(limit)
        
        # Filter by symbol
        if symbol:
            trades = [t for t in trades if t.get('symbol') == symbol]
        
        return jsonify({
            'success': True,
            'trades': trades,
            'count': len(trades)
        })
        
    except Exception as e:
        logger.error(f"Journal error: {e}")
        return jsonify({
            'success': True,
            'trades': [],
            'count': 0
        })


@trading_api.route('/journal/trades', methods=['POST'])
def log_trade():
    """Log a new trade entry."""
    try:
        data = request.get_json()
        
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        trade_id = journal.log_trade_entry(
            symbol=data.get('symbol'),
            side=data.get('side'),
            entry_price=float(data.get('entry_price')),
            quantity=float(data.get('quantity')),
            leverage=int(data.get('leverage', 1)),
            signal_type=data.get('signal_type', ''),
            signal_confidence=float(data.get('signal_confidence', 0)),
            strategy=data.get('strategy', ''),
            timeframe=data.get('timeframe', ''),
            exchange=data.get('exchange', ''),
            account_id=data.get('account_id', ''),
            stop_loss=float(data.get('stop_loss')) if data.get('stop_loss') else None,
            take_profit=float(data.get('take_profit')) if data.get('take_profit') else None,
            notes=data.get('notes', ''),
            tags=data.get('tags', [])
        )
        
        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'message': 'Trade logged'
        })
        
    except Exception as e:
        logger.error(f"Trade log error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/journal/trades/<trade_id>/close', methods=['POST'])
def close_trade(trade_id: str):
    """Close a trade."""
    try:
        data = request.get_json()
        
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        trade = journal.log_trade_exit(
            trade_id=trade_id,
            exit_price=float(data.get('exit_price')),
            fees=float(data.get('fees', 0)),
            notes=data.get('notes', '')
        )
        
        if trade:
            return jsonify({
                'success': True,
                'trade': trade.to_dict(),
                'message': 'Trade closed'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Trade not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/journal/trades/<trade_id>', methods=['GET'])
def get_trade(trade_id: str):
    """Get trade by ID."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        trade = journal.get_trade(trade_id)
        
        if trade:
            return jsonify({
                'success': True,
                'trade': trade
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Trade not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ========================
# Reports Endpoints
# ========================

@trading_api.route('/reports/metrics', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics."""
    try:
        days = int(request.args.get('days', 30))
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        start_date = datetime.now() - timedelta(days=days) if days > 0 else None
        
        metrics = journal.calculate_metrics(
            start_date=start_date,
            symbol=symbol,
            strategy=strategy
        )
        
        return jsonify({
            'success': True,
            'metrics': metrics.to_dict(),
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({
            'success': True,
            'metrics': {}
        })


@trading_api.route('/reports/equity-curve', methods=['GET'])
def get_equity_curve():
    """Get equity curve data."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        return jsonify({
            'success': True,
            'equity_curve': journal.get_equity_curve()
        })
        
    except Exception as e:
        return jsonify({
            'success': True,
            'equity_curve': []
        })


@trading_api.route('/reports/daily-pnl', methods=['GET'])
def get_daily_pnl():
    """Get daily P&L."""
    try:
        days = int(request.args.get('days', 30))
        
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        return jsonify({
            'success': True,
            'daily_pnl': journal.get_daily_pnl(days)
        })
        
    except Exception as e:
        return jsonify({
            'success': True,
            'daily_pnl': []
        })


@trading_api.route('/reports/symbols', methods=['GET'])
def get_symbol_stats():
    """Get stats by symbol."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        return jsonify({
            'success': True,
            'symbol_stats': journal.get_symbol_stats()
        })
        
    except Exception as e:
        return jsonify({
            'success': True,
            'symbol_stats': []
        })


@trading_api.route('/reports/export/csv', methods=['GET'])
def export_csv():
    """Export trades to CSV."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        filepath = journal.export_to_csv()
        
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'trades_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/reports/export/json', methods=['GET'])
def export_json():
    """Export journal to JSON."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        filepath = journal.export_to_json()
        
        return send_file(
            filepath,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'journal_{datetime.now().strftime("%Y%m%d")}.json'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@trading_api.route('/reports/summary', methods=['GET'])
def get_summary():
    """Get trading summary."""
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        
        # Get metrics for different periods
        all_time = journal.calculate_metrics()
        last_30 = journal.calculate_metrics(start_date=datetime.now() - timedelta(days=30))
        last_7 = journal.calculate_metrics(start_date=datetime.now() - timedelta(days=7))
        today = journal.calculate_metrics(start_date=datetime.now().replace(hour=0, minute=0, second=0))
        
        # Get equity
        equity_curve = journal.get_equity_curve()
        current_equity = equity_curve[-1]['equity'] if equity_curve else journal.initial_capital
        
        return jsonify({
            'success': True,
            'summary': {
                'current_equity': round(current_equity, 2),
                'initial_capital': journal.initial_capital,
                'total_return_pct': round((current_equity - journal.initial_capital) / journal.initial_capital * 100, 2),
                'open_trades': len(journal.get_open_trades()),
                'periods': {
                    'all_time': all_time.to_dict(),
                    'last_30_days': last_30.to_dict(),
                    'last_7_days': last_7.to_dict(),
                    'today': today.to_dict()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Summary error: {e}")
        return jsonify({
            'success': True,
            'summary': {
                'current_equity': 10000,
                'initial_capital': 10000,
                'total_return_pct': 0,
                'open_trades': 0
            }
        })


def register_trading_routes(app):
    """Register trading API routes with Flask app."""
    app.register_blueprint(trading_api)
    logger.info("Trading API routes registered")
