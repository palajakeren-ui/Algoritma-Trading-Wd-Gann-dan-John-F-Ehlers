"""
Multi-Account Trading System
Complete multi-account, multi-exchange management with account-aware execution.
"""
import numpy as np
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import threading


class AccountStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ERROR = "error"


class BrokerType(Enum):
    CRYPTO_EXCHANGE = "crypto_exchange"
    METATRADER = "metatrader"
    FIX_PROTOCOL = "fix"


@dataclass
class AccountBalance:
    """Account balance snapshot."""
    total: float
    available: float
    used: float
    unrealized_pnl: float = 0.0
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradingAccount:
    """Complete trading account configuration."""
    id: str
    name: str
    broker_type: BrokerType
    exchange: str
    account_type: str  # spot, futures, margin
    credential_id: str
    
    # Status
    status: AccountStatus = AccountStatus.INACTIVE
    is_live: bool = False
    is_default: bool = False
    
    # Configuration
    max_leverage: int = 1
    max_position_size_pct: float = 10.0
    risk_per_trade_pct: float = 2.0
    max_daily_loss_pct: float = 5.0
    
    # Balance
    balance: AccountBalance = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_sync: datetime = None
    last_trade: datetime = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'broker_type': self.broker_type.value,
            'exchange': self.exchange,
            'account_type': self.account_type,
            'status': self.status.value,
            'is_live': self.is_live,
            'is_default': self.is_default,
            'max_leverage': self.max_leverage,
            'max_position_size_pct': self.max_position_size_pct,
            'risk_per_trade_pct': self.risk_per_trade_pct,
            'balance': {
                'total': self.balance.total if self.balance else 0,
                'available': self.balance.available if self.balance else 0,
                'currency': self.balance.currency if self.balance else 'USD'
            } if self.balance else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat()
        }


class MultiAccountManager:
    """
    Multi-Account Trading System.
    
    Features:
    - Multiple accounts per exchange
    - Multiple exchanges per user
    - Account ↔ Broker ↔ Credential mapping
    - Account-aware execution
    - Unified balance aggregation
    - Cross-account position tracking
    """
    
    def __init__(self):
        # Account storage: account_id -> TradingAccount
        self.accounts: Dict[str, TradingAccount] = {}
        
        # Exchange grouping: exchange -> [account_ids]
        self.accounts_by_exchange: Dict[str, List[str]] = {}
        
        # Broker grouping: broker_type -> [account_ids]
        self.accounts_by_broker: Dict[str, List[str]] = {}
        
        # Connectors: account_id -> connector
        self._connectors: Dict[str, Any] = {}
        
        # Security vault reference
        self._vault = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        logger.info("MultiAccountManager initialized")
    
    def set_vault(self, vault):
        """Set security vault for credential access."""
        self._vault = vault
    
    # ========================
    # Account Management
    # ========================
    
    def add_account(
        self,
        name: str,
        broker_type: BrokerType,
        exchange: str,
        account_type: str,
        credential_id: str,
        is_live: bool = False,
        is_default: bool = False,
        max_leverage: int = 1,
        **kwargs
    ) -> str:
        """
        Add a new trading account.
        
        Args:
            name: Display name for account
            broker_type: Type of broker (crypto/mt/fix)
            exchange: Exchange identifier
            account_type: spot/futures/margin
            credential_id: Reference to encrypted credentials
            is_live: Whether this is a live account
            is_default: Set as default for this exchange
            max_leverage: Maximum allowed leverage
            
        Returns:
            Account ID
        """
        with self._lock:
            account_id = f"ACC_{exchange}_{int(datetime.now().timestamp() * 1000)}"
            
            account = TradingAccount(
                id=account_id,
                name=name,
                broker_type=broker_type,
                exchange=exchange,
                account_type=account_type,
                credential_id=credential_id,
                is_live=is_live,
                is_default=is_default,
                max_leverage=max_leverage,
                max_position_size_pct=kwargs.get('max_position_size_pct', 10.0),
                risk_per_trade_pct=kwargs.get('risk_per_trade_pct', 2.0),
                max_daily_loss_pct=kwargs.get('max_daily_loss_pct', 5.0),
                metadata=kwargs.get('metadata', {})
            )
            
            # Store account
            self.accounts[account_id] = account
            
            # Index by exchange
            if exchange not in self.accounts_by_exchange:
                self.accounts_by_exchange[exchange] = []
            self.accounts_by_exchange[exchange].append(account_id)
            
            # Index by broker
            broker_key = broker_type.value
            if broker_key not in self.accounts_by_broker:
                self.accounts_by_broker[broker_key] = []
            self.accounts_by_broker[broker_key].append(account_id)
            
            # If default, unset other defaults for this exchange
            if is_default:
                for acc_id in self.accounts_by_exchange.get(exchange, []):
                    if acc_id != account_id:
                        self.accounts[acc_id].is_default = False
            
            logger.info(f"Added account: {account_id} ({name}) on {exchange}")
            
            return account_id
    
    def remove_account(self, account_id: str) -> bool:
        """Remove an account."""
        with self._lock:
            if account_id not in self.accounts:
                return False
            
            account = self.accounts[account_id]
            
            # Disconnect if connected
            if account_id in self._connectors:
                self._disconnect_account(account_id)
            
            # Remove from indexes
            exchange = account.exchange
            broker = account.broker_type.value
            
            if exchange in self.accounts_by_exchange:
                self.accounts_by_exchange[exchange].remove(account_id)
            
            if broker in self.accounts_by_broker:
                self.accounts_by_broker[broker].remove(account_id)
            
            # Remove account
            del self.accounts[account_id]
            
            logger.info(f"Removed account: {account_id}")
            
            return True
    
    def get_account(self, account_id: str) -> Optional[TradingAccount]:
        """Get account by ID."""
        return self.accounts.get(account_id)
    
    def get_accounts_for_exchange(self, exchange: str) -> List[TradingAccount]:
        """Get all accounts for an exchange."""
        account_ids = self.accounts_by_exchange.get(exchange, [])
        return [self.accounts[aid] for aid in account_ids if aid in self.accounts]
    
    def get_accounts_for_broker(self, broker_type: str) -> List[TradingAccount]:
        """Get all accounts for a broker type."""
        account_ids = self.accounts_by_broker.get(broker_type, [])
        return [self.accounts[aid] for aid in account_ids if aid in self.accounts]
    
    def get_default_account(self, exchange: str = None) -> Optional[TradingAccount]:
        """Get default account for an exchange."""
        if exchange:
            for acc_id in self.accounts_by_exchange.get(exchange, []):
                if self.accounts[acc_id].is_default:
                    return self.accounts[acc_id]
        
        # Return any default account
        for acc in self.accounts.values():
            if acc.is_default:
                return acc
        
        # Return first account
        if self.accounts:
            return list(self.accounts.values())[0]
        
        return None
    
    def get_all_accounts(self) -> List[TradingAccount]:
        """Get all accounts."""
        return list(self.accounts.values())
    
    def set_default_account(self, account_id: str) -> bool:
        """Set an account as default."""
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        # Unset other defaults for same exchange
        for acc_id in self.accounts_by_exchange.get(account.exchange, []):
            self.accounts[acc_id].is_default = (acc_id == account_id)
        
        return True
    
    # ========================
    # Account Connection
    # ========================
    
    async def connect_account(self, account_id: str) -> bool:
        """Connect an account."""
        if account_id not in self.accounts:
            logger.error(f"Account not found: {account_id}")
            return False
        
        account = self.accounts[account_id]
        
        # Get credentials from vault
        if self._vault and account.credential_id:
            credentials = self._vault.get_credential(account.credential_id)
            if not credentials:
                logger.error(f"Credentials not found for account: {account_id}")
                return False
        else:
            logger.warning(f"No vault or credential_id for account: {account_id}")
            credentials = {}
        
        try:
            # Create connector based on broker type
            connector = None
            
            if account.broker_type == BrokerType.CRYPTO_EXCHANGE:
                from connectors.exchange_connector import ExchangeConnectorFactory, ExchangeCredentials
                
                creds = ExchangeCredentials(
                    api_key=credentials.get('api_key', ''),
                    api_secret=credentials.get('api_secret', ''),
                    passphrase=credentials.get('passphrase', ''),
                    testnet=not account.is_live
                )
                
                connector = ExchangeConnectorFactory.create(
                    exchange_id=account.exchange,
                    credentials=creds,
                    account_id=account_id,
                    mode=account.account_type
                )
                
            elif account.broker_type == BrokerType.METATRADER:
                from connectors.metatrader_connector import MetaTraderConnector, MTCredentials, MTVersion
                
                version = MTVersion.MT5 if 'mt5' in account.exchange.lower() else MTVersion.MT4
                
                creds = MTCredentials(
                    login=credentials.get('login', ''),
                    password=credentials.get('password', ''),
                    server=credentials.get('server', ''),
                    version=version,
                    account_type='live' if account.is_live else 'demo',
                    broker=credentials.get('broker', '')
                )
                
                connector = MetaTraderConnector(creds, account_id)
                
            elif account.broker_type == BrokerType.FIX_PROTOCOL:
                from connectors.fix_connector import FIXConnector, FIXCredentials, FIXVersion
                
                creds = FIXCredentials(
                    host=credentials.get('host', ''),
                    port=int(credentials.get('port', 443)),
                    sender_comp_id=credentials.get('sender_comp_id', ''),
                    target_comp_id=credentials.get('target_comp_id', ''),
                    username=credentials.get('username', ''),
                    password=credentials.get('password', ''),
                    ssl_enabled=credentials.get('ssl_enabled', True)
                )
                
                connector = FIXConnector(creds, account_id)
            
            if connector:
                # Connect
                connected = await connector.connect()
                
                if connected:
                    self._connectors[account_id] = connector
                    account.status = AccountStatus.ACTIVE
                    account.last_sync = datetime.now()
                    
                    # Fetch initial balance
                    await self.sync_account_balance(account_id)
                    
                    logger.success(f"Account connected: {account_id}")
                    return True
                else:
                    account.status = AccountStatus.ERROR
                    return False
            
        except Exception as e:
            logger.error(f"Failed to connect account {account_id}: {e}")
            account.status = AccountStatus.ERROR
            return False
        
        return False
    
    async def disconnect_account(self, account_id: str) -> bool:
        """Disconnect an account."""
        return self._disconnect_account(account_id)
    
    def _disconnect_account(self, account_id: str) -> bool:
        """Internal disconnect."""
        if account_id in self._connectors:
            connector = self._connectors[account_id]
            
            try:
                if hasattr(connector, 'disconnect'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(connector.disconnect())
                    loop.close()
            except:
                pass
            
            del self._connectors[account_id]
        
        if account_id in self.accounts:
            self.accounts[account_id].status = AccountStatus.INACTIVE
        
        logger.info(f"Account disconnected: {account_id}")
        return True
    
    def is_account_connected(self, account_id: str) -> bool:
        """Check if account is connected."""
        return account_id in self._connectors
    
    def get_connector(self, account_id: str):
        """Get connector for account."""
        return self._connectors.get(account_id)
    
    # ========================
    # Balance & Sync
    # ========================
    
    async def sync_account_balance(self, account_id: str) -> Optional[AccountBalance]:
        """Sync account balance from exchange."""
        if account_id not in self._connectors:
            return None
        
        connector = self._connectors[account_id]
        account = self.accounts.get(account_id)
        
        if not account:
            return None
        
        try:
            balances = await connector.get_balance()
            
            if balances:
                # Aggregate balance (use primary currency)
                total = sum(b.total for b in balances)
                free = sum(b.free for b in balances)
                used = sum(b.used for b in balances)
                
                # Find primary currency
                currency = "USD"
                for b in balances:
                    if b.currency in ['USDT', 'USD', 'USDC']:
                        currency = b.currency
                        break
                
                balance = AccountBalance(
                    total=total,
                    available=free,
                    used=used,
                    currency=currency
                )
                
                account.balance = balance
                account.last_sync = datetime.now()
                
                return balance
                
        except Exception as e:
            logger.error(f"Failed to sync balance for {account_id}: {e}")
        
        return None
    
    async def sync_all_accounts(self):
        """Sync all connected accounts."""
        for account_id in self._connectors:
            await self.sync_account_balance(account_id)
    
    def get_total_balance(self) -> Dict[str, float]:
        """Get aggregated balance across all accounts."""
        totals = {}
        
        for account in self.accounts.values():
            if account.balance:
                currency = account.balance.currency
                if currency not in totals:
                    totals[currency] = 0
                totals[currency] += account.balance.total
        
        return totals
    
    # ========================
    # Account-Aware Execution
    # ========================
    
    async def execute_on_account(
        self,
        account_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        **kwargs
    ) -> Dict:
        """Execute order on specific account."""
        if account_id not in self._connectors:
            return {
                'success': False,
                'error': 'Account not connected'
            }
        
        account = self.accounts.get(account_id)
        connector = self._connectors[account_id]
        
        if not account:
            return {
                'success': False,
                'error': 'Account not found'
            }
        
        # Apply account-specific risk limits
        if account.balance:
            position_value = quantity * (price or 0)
            max_position = account.balance.available * (account.max_position_size_pct / 100)
            
            if position_value > max_position:
                return {
                    'success': False,
                    'error': f'Position size exceeds account limit ({account.max_position_size_pct}%)'
                }
        
        try:
            from connectors.exchange_connector import Order, OrderSide, OrderType
            
            order = Order(
                id="",
                client_order_id=f"MA_{account_id}_{int(datetime.now().timestamp() * 1000)}",
                symbol=symbol,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                type=OrderType.MARKET if order_type.lower() == 'market' else OrderType.LIMIT,
                amount=quantity,
                price=price,
                leverage=min(kwargs.get('leverage', 1), account.max_leverage)
            )
            
            executed = await connector.create_order(order)
            
            # Update last trade time
            account.last_trade = datetime.now()
            
            return {
                'success': executed.status.value in ['open', 'filled'],
                'order_id': executed.id,
                'status': executed.status.value,
                'filled': executed.filled,
                'average_price': executed.average_price
            }
            
        except Exception as e:
            logger.error(f"Execution error on {account_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_on_all_accounts(
        self,
        exchange: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity_per_account: float,
        price: float = None,
        **kwargs
    ) -> List[Dict]:
        """Execute same order on all accounts for an exchange."""
        results = []
        
        for account_id in self.accounts_by_exchange.get(exchange, []):
            if account_id in self._connectors:
                result = await self.execute_on_account(
                    account_id=account_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity_per_account,
                    price=price,
                    **kwargs
                )
                result['account_id'] = account_id
                results.append(result)
        
        return results
    
    # ========================
    # Serialization
    # ========================
    
    def to_dict(self) -> Dict:
        """Serialize to dict for API response."""
        return {
            'accounts': [acc.to_dict() for acc in self.accounts.values()],
            'exchanges': list(self.accounts_by_exchange.keys()),
            'brokers': list(self.accounts_by_broker.keys()),
            'connected_count': len(self._connectors),
            'total_balance': self.get_total_balance()
        }
    
    def save_to_file(self, filepath: str):
        """Save accounts to file."""
        data = {
            'accounts': [acc.to_dict() for acc in self.accounts.values()],
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load accounts from file."""
        import os
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for acc_data in data.get('accounts', []):
            # Recreate account
            self.add_account(
                name=acc_data['name'],
                broker_type=BrokerType(acc_data['broker_type']),
                exchange=acc_data['exchange'],
                account_type=acc_data['account_type'],
                credential_id=acc_data.get('credential_id', ''),
                is_live=acc_data.get('is_live', False),
                is_default=acc_data.get('is_default', False),
                max_leverage=acc_data.get('max_leverage', 1)
            )


# Global instance
_account_manager: Optional[MultiAccountManager] = None


def get_multi_account_manager() -> MultiAccountManager:
    """Get or create multi-account manager."""
    global _account_manager
    if _account_manager is None:
        _account_manager = MultiAccountManager()
    return _account_manager


if __name__ == "__main__":
    # Test multi-account system
    manager = MultiAccountManager()
    
    # Add accounts
    acc1 = manager.add_account(
        name="Binance Futures Demo",
        broker_type=BrokerType.CRYPTO_EXCHANGE,
        exchange="binance",
        account_type="futures",
        credential_id="cred_1",
        is_live=False,
        is_default=True,
        max_leverage=20
    )
    
    acc2 = manager.add_account(
        name="Bybit Spot",
        broker_type=BrokerType.CRYPTO_EXCHANGE,
        exchange="bybit",
        account_type="spot",
        credential_id="cred_2"
    )
    
    acc3 = manager.add_account(
        name="MT5 Forex",
        broker_type=BrokerType.METATRADER,
        exchange="mt5",
        account_type="forex",
        credential_id="cred_3"
    )
    
    print("\n=== Multi-Account System ===")
    print(f"Total accounts: {len(manager.get_all_accounts())}")
    print(f"Exchanges: {list(manager.accounts_by_exchange.keys())}")
    print(f"Brokers: {list(manager.accounts_by_broker.keys())}")
    
    for acc in manager.get_all_accounts():
        print(f"\n{acc.name}:")
        print(f"  ID: {acc.id}")
        print(f"  Exchange: {acc.exchange}")
        print(f"  Type: {acc.account_type}")
        print(f"  Live: {acc.is_live}")
        print(f"  Default: {acc.is_default}")
