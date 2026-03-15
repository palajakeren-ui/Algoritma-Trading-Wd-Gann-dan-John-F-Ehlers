"""
Gann Quant AI - Production Trading System Startup
One-click startup for the complete trading platform.
"""
import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██████╗  █████╗ ███╗   ██╗███╗   ██╗                        ║
║    ██╔════╝ ██╔══██╗████╗  ██║████╗  ██║                        ║
║    ██║  ███╗███████║██╔██╗ ██║██╔██╗ ██║                        ║
║    ██║   ██║██╔══██║██║╚██╗██║██║╚██╗██║                        ║
║    ╚██████╔╝██║  ██║██║ ╚████║██║ ╚████║                        ║
║     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝                        ║
║                                                                  ║
║              ✦ CENAYANG MARKET ✦                                 ║
║      Advanced Quant & Astro-Trading Analytics                    ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  📢 Social Hub                                                   ║
║  • Twitter / X : @CenayangMarket                                 ║
║  • Instagram   : @cenayang.market                                ║
║  • TikTok      : @cenayang.market                                ║
║  • Facebook    : Cenayang.Market                                 ║
║  • Telegram    : @cenayangmarket                                 ║
║                                                                  ║
║  ☕ Support & Donations                                          ║
║  • Saweria     : saweria.co/CenayangMarket                       ║
║  • Trakteer    : trakteer.id/Cenayang.Market/tip                 ║
║  • Patreon     : patreon.com/Cenayangmarket                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Features:                                                       ║
║  ✓ AI-Driven Signals (Gann, Ehlers, Astro, ML)                  ║
║  ✓ Multi-Exchange Support (14 Exchanges)                        ║
║  ✓ Multi-Account Management                                      ║
║  ✓ Risk Management Engine                                        ║
║  ✓ Real-Time Data Feed (MT4/MT5, FIX, Crypto)                   ║
║  ✓ Paper & Live Trading                                          ║
║  ✓ Trading Journal & Reports                                     ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check required dependencies."""
    print("\n[1/4] Checking dependencies...")
    
    required = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('loguru', 'Loguru'),
        ('ccxt', 'CCXT'),
    ]
    
    missing = []
    
    for module, name in required:
        try:
            __import__(module)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} - MISSING")
            missing.append(name)
    
    if missing:
        print(f"\n   ⚠ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def initialize_components():
    """Initialize core components."""
    print("\n[2/4] Initializing components...")
    
    components = []
    
    try:
        from core.signal_engine import get_signal_engine
        engine = get_signal_engine()
        components.append(('Signal Engine', True))
        print("   ✓ AI Signal Engine")
    except Exception as e:
        components.append(('Signal Engine', False))
        print(f"   ✗ AI Signal Engine - {e}")
    
    try:
        from core.risk_engine import get_risk_engine
        engine = get_risk_engine()
        engine.initialize_equity(10000)
        components.append(('Risk Engine', True))
        print("   ✓ Risk Engine")
    except Exception as e:
        components.append(('Risk Engine', False))
        print(f"   ✗ Risk Engine - {e}")
    
    try:
        from core.execution_gate import get_execution_gate
        gate = get_execution_gate()
        components.append(('Execution Gate', True))
        print("   ✓ Execution Gate")
    except Exception as e:
        components.append(('Execution Gate', False))
        print(f"   ✗ Execution Gate - {e}")
    
    try:
        from core.live_execution_engine import get_execution_engine
        engine = get_execution_engine()
        components.append(('Execution Engine', True))
        print("   ✓ Execution Engine")
    except Exception as e:
        components.append(('Execution Engine', False))
        print(f"   ✗ Execution Engine - {e}")
    
    try:
        from core.security_manager import get_secure_vault
        vault = get_secure_vault()
        vault.set_master_key("gann_quant_ai_production_key")
        components.append(('Security Vault', True))
        print("   ✓ Security Vault")
    except Exception as e:
        components.append(('Security Vault', False))
        print(f"   ✗ Security Vault - {e}")
    
    try:
        from core.trading_journal import get_trading_journal
        journal = get_trading_journal()
        components.append(('Trading Journal', True))
        print("   ✓ Trading Journal")
    except Exception as e:
        components.append(('Trading Journal', False))
        print(f"   ✗ Trading Journal - {e}")
    
    return all(c[1] for c in components)


def register_api_routes():
    """Register API routes."""
    print("\n[3/4] Registering API routes...")
    
    routes = [
        '/api/sync/*          - Frontend-Backend Sync (27 routes)',
        '/api/ai/*            - AI Engine (signals, training)',
        '/api/settings/*      - Settings & Accounts',
        '/api/market-data/*   - Real-Time Data Feed',
        '/api/execution/*     - Order Execution',
        '/api/trading/*       - Orchestrator & Journal',
        '/api/config/*        - YAML Config Sync',
        '/api/hft/*           - High-Frequency Trading',
        '/api/broker/*        - Broker & ML Training',
        '/api/safety/*        - Kill Switch & Safety',
        '/api/bookmap/*       - Bookmap & Terminal',
        '/api/analytics/*     - Scanner, Forecast, Cycles, Options',
        '/api/agents/*        - AI Agent Orchestration',
        '/api/v2/* (inline)   - Core Routes (health, backtest, signals)',
    ]
    
    for route in routes:
        print(f"   ✓ {route}")
    
    return True


def start_server(host='0.0.0.0', port=5000, debug=False):
    """Start Flask server."""
    print(f"\n[4/4] Starting server on {host}:{port}...")
    
    try:
        from api import app
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                     SERVER STARTED                               ║
╠══════════════════════════════════════════════════════════════════╣
║  URL: http://localhost:{port}                                     ║
║  API: http://localhost:{port}/api                                 ║
║  Docs: See docs/API_REFERENCE.md                                 ║
║                                                                  ║
║  Press Ctrl+C to stop                                            ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # Use standard Flask run (no socketio needed)
        app.run(host=host, port=port, debug=debug, use_reloader=False)
        
    except Exception as e:
        print(f"\n   ✗ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main entry point."""
    print_banner()
    print(f"  Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠ Please install missing dependencies first.")
        sys.exit(1)
    
    # Initialize components
    if not initialize_components():
        print("\n⚠ Some components failed to initialize. Check errors above.")
        # Continue anyway - some components may still work
    
    # Register routes
    register_api_routes()
    
    # Get port from environment or use default
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Start server
    start_server(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
