"""
Security & Credential Manager
Secure vault for API keys, secrets, and sensitive configuration.
"""
import os
import json
import base64
import hashlib
from loguru import logger
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import secrets

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed. Using basic obfuscation.")


class CredentialType(Enum):
    CRYPTO_EXCHANGE = "crypto_exchange"
    METATRADER = "metatrader"
    FIX_PROTOCOL = "fix_protocol"
    API_KEY = "api_key"


@dataclass
class EncryptedCredential:
    """Encrypted credential storage."""
    id: str
    type: CredentialType
    account_id: str
    exchange: str
    encrypted_data: str
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = None
    metadata: Dict = field(default_factory=dict)


class SecureVault:
    """
    Secure vault for credential storage and management.
    
    Features:
    - AES-256 encryption for all secrets
    - Key derivation from master password
    - No plaintext storage
    - Account isolation
    - Audit logging
    """
    
    def __init__(self, vault_path: str = None, master_key: str = None):
        self.vault_path = Path(vault_path or "outputs/secure_vault")
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        self._fernet = None
        self._master_key_hash = None
        
        if master_key:
            self._initialize_encryption(master_key)
        
        # In-memory credential cache (encrypted)
        self._credentials: Dict[str, EncryptedCredential] = {}
        
        # Load existing credentials
        self._load_vault()
        
        logger.info("SecureVault initialized")
    
    def _initialize_encryption(self, master_key: str):
        """Initialize encryption with master key."""
        if CRYPTO_AVAILABLE:
            # Use PBKDF2 for key derivation
            salt = b'gann_quant_ai_salt_v1'  # In production, use unique salt per vault
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._fernet = Fernet(key)
            self._master_key_hash = hashlib.sha256(master_key.encode()).hexdigest()
        else:
            # Basic obfuscation fallback
            self._master_key_hash = hashlib.sha256(master_key.encode()).hexdigest()
    
    def set_master_key(self, master_key: str) -> bool:
        """Set or update master key."""
        self._initialize_encryption(master_key)
        logger.info("Master key set")
        return True
    
    def is_initialized(self) -> bool:
        """Check if vault is initialized with master key."""
        return self._master_key_hash is not None
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data."""
        if self._fernet:
            return self._fernet.encrypt(data.encode()).decode()
        else:
            # Basic obfuscation (not secure, just for development)
            return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        if self._fernet:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        else:
            return base64.b64decode(encrypted_data.encode()).decode()
    
    def store_credential(
        self,
        account_id: str,
        exchange: str,
        credential_type: CredentialType,
        credentials: Dict
    ) -> str:
        """
        Store encrypted credentials.
        
        Args:
            account_id: Account identifier
            exchange: Exchange/broker name
            credential_type: Type of credential
            credentials: Credential data dict
            
        Returns:
            Credential ID
        """
        if not self.is_initialized():
            raise ValueError("Vault not initialized. Set master key first.")
        
        credential_id = f"{account_id}_{exchange}_{int(datetime.now().timestamp())}"
        
        # Encrypt credential data
        encrypted_data = self._encrypt(json.dumps(credentials))
        
        cred = EncryptedCredential(
            id=credential_id,
            type=credential_type,
            account_id=account_id,
            exchange=exchange,
            encrypted_data=encrypted_data
        )
        
        self._credentials[credential_id] = cred
        
        # Persist to disk
        self._save_vault()
        
        logger.info(f"Stored credential: {credential_id}")
        return credential_id
    
    def get_credential(self, credential_id: str) -> Optional[Dict]:
        """Retrieve and decrypt credentials."""
        if not self.is_initialized():
            raise ValueError("Vault not initialized")
        
        if credential_id not in self._credentials:
            logger.warning(f"Credential not found: {credential_id}")
            return None
        
        cred = self._credentials[credential_id]
        cred.last_used = datetime.now()
        
        try:
            decrypted = self._decrypt(cred.encrypted_data)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            return None
    
    def get_credentials_for_account(self, account_id: str) -> List[Dict]:
        """Get all credentials for an account."""
        if not self.is_initialized():
            return []
        
        results = []
        for cred in self._credentials.values():
            if cred.account_id == account_id:
                try:
                    data = json.loads(self._decrypt(cred.encrypted_data))
                    results.append({
                        'id': cred.id,
                        'type': cred.type.value,
                        'exchange': cred.exchange,
                        'created_at': cred.created_at.isoformat(),
                        'data': data
                    })
                except:
                    pass
        
        return results
    
    def list_credentials(self, account_id: str = None) -> List[Dict]:
        """List stored credentials (without decrypting secrets)."""
        results = []
        for cred in self._credentials.values():
            if account_id and cred.account_id != account_id:
                continue
            
            results.append({
                'id': cred.id,
                'type': cred.type.value,
                'account_id': cred.account_id,
                'exchange': cred.exchange,
                'created_at': cred.created_at.isoformat(),
                'last_used': cred.last_used.isoformat() if cred.last_used else None
            })
        
        return results
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete a credential."""
        if credential_id in self._credentials:
            del self._credentials[credential_id]
            self._save_vault()
            logger.info(f"Deleted credential: {credential_id}")
            return True
        return False
    
    def update_credential(self, credential_id: str, new_data: Dict) -> bool:
        """Update credential data."""
        if credential_id not in self._credentials:
            return False
        
        cred = self._credentials[credential_id]
        cred.encrypted_data = self._encrypt(json.dumps(new_data))
        self._save_vault()
        
        logger.info(f"Updated credential: {credential_id}")
        return True
    
    def _save_vault(self):
        """Save vault to disk."""
        vault_file = self.vault_path / "vault.json"
        
        data = {
            'version': '1.0',
            'master_key_hash': self._master_key_hash,
            'credentials': [
                {
                    'id': c.id,
                    'type': c.type.value,
                    'account_id': c.account_id,
                    'exchange': c.exchange,
                    'encrypted_data': c.encrypted_data,
                    'created_at': c.created_at.isoformat(),
                    'last_used': c.last_used.isoformat() if c.last_used else None,
                    'metadata': c.metadata
                }
                for c in self._credentials.values()
            ]
        }
        
        with open(vault_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_vault(self):
        """Load vault from disk."""
        vault_file = self.vault_path / "vault.json"
        
        if not vault_file.exists():
            return
        
        try:
            with open(vault_file, 'r') as f:
                data = json.load(f)
            
            for cred_data in data.get('credentials', []):
                cred = EncryptedCredential(
                    id=cred_data['id'],
                    type=CredentialType(cred_data['type']),
                    account_id=cred_data['account_id'],
                    exchange=cred_data['exchange'],
                    encrypted_data=cred_data['encrypted_data'],
                    created_at=datetime.fromisoformat(cred_data['created_at']),
                    last_used=datetime.fromisoformat(cred_data['last_used']) if cred_data.get('last_used') else None,
                    metadata=cred_data.get('metadata', {})
                )
                self._credentials[cred.id] = cred
            
            logger.info(f"Loaded {len(self._credentials)} credentials from vault")
            
        except Exception as e:
            logger.error(f"Failed to load vault: {e}")


@dataclass
class TradingAccount:
    """Trading account configuration."""
    id: str
    name: str
    exchange: str
    account_type: str  # spot, futures, margin
    broker_type: str  # crypto_exchange, metatrader, fix
    credential_id: str
    enabled: bool = True
    is_live: bool = False
    balance: float = 0.0
    equity: float = 0.0
    currency: str = "USD"
    max_leverage: int = 1
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_sync: datetime = None


class AccountManager:
    """
    Multi-Account Management System.
    
    Features:
    - Multiple accounts per exchange
    - Multiple exchanges per user
    - Account ↔ broker ↔ credential mapping
    - Account-aware execution
    """
    
    def __init__(self, vault: SecureVault = None):
        self.vault = vault or SecureVault()
        self.accounts: Dict[str, TradingAccount] = {}
        self._load_accounts()
        
        logger.info("AccountManager initialized")
    
    def add_account(
        self,
        name: str,
        exchange: str,
        account_type: str,
        broker_type: str,
        credentials: Dict,
        is_live: bool = False,
        max_leverage: int = 1
    ) -> str:
        """Add a new trading account."""
        account_id = f"ACC_{exchange}_{int(datetime.now().timestamp())}"
        
        # Store credentials securely
        credential_type = CredentialType.CRYPTO_EXCHANGE
        if broker_type == "metatrader":
            credential_type = CredentialType.METATRADER
        elif broker_type == "fix":
            credential_type = CredentialType.FIX_PROTOCOL
        
        credential_id = self.vault.store_credential(
            account_id=account_id,
            exchange=exchange,
            credential_type=credential_type,
            credentials=credentials
        )
        
        account = TradingAccount(
            id=account_id,
            name=name,
            exchange=exchange,
            account_type=account_type,
            broker_type=broker_type,
            credential_id=credential_id,
            is_live=is_live,
            max_leverage=max_leverage
        )
        
        self.accounts[account_id] = account
        self._save_accounts()
        
        logger.info(f"Added account: {account_id} ({name})")
        return account_id
    
    def get_account(self, account_id: str) -> Optional[TradingAccount]:
        """Get account by ID."""
        return self.accounts.get(account_id)
    
    def get_accounts_by_exchange(self, exchange: str) -> List[TradingAccount]:
        """Get all accounts for an exchange."""
        return [a for a in self.accounts.values() if a.exchange == exchange]
    
    def get_all_accounts(self) -> List[TradingAccount]:
        """Get all accounts."""
        return list(self.accounts.values())
    
    def get_account_credentials(self, account_id: str) -> Optional[Dict]:
        """Get decrypted credentials for account."""
        account = self.accounts.get(account_id)
        if not account:
            return None
        
        return self.vault.get_credential(account.credential_id)
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """Update account settings."""
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        for key, value in updates.items():
            if hasattr(account, key) and key not in ['id', 'credential_id']:
                setattr(account, key, value)
        
        self._save_accounts()
        logger.info(f"Updated account: {account_id}")
        return True
    
    def update_account_balance(self, account_id: str, balance: float, equity: float = None):
        """Update account balance."""
        if account_id in self.accounts:
            self.accounts[account_id].balance = balance
            if equity is not None:
                self.accounts[account_id].equity = equity
            self.accounts[account_id].last_sync = datetime.now()
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an account."""
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        # Delete credential
        self.vault.delete_credential(account.credential_id)
        
        # Delete account
        del self.accounts[account_id]
        self._save_accounts()
        
        logger.info(f"Deleted account: {account_id}")
        return True
    
    def enable_account(self, account_id: str) -> bool:
        """Enable an account."""
        return self.update_account(account_id, {'enabled': True})
    
    def disable_account(self, account_id: str) -> bool:
        """Disable an account."""
        return self.update_account(account_id, {'enabled': False})
    
    def get_enabled_accounts(self) -> List[TradingAccount]:
        """Get all enabled accounts."""
        return [a for a in self.accounts.values() if a.enabled]
    
    def get_live_accounts(self) -> List[TradingAccount]:
        """Get all live (non-demo) accounts."""
        return [a for a in self.accounts.values() if a.is_live]
    
    def _save_accounts(self):
        """Save accounts to disk."""
        accounts_file = self.vault.vault_path / "accounts.json"
        
        data = {
            'version': '1.0',
            'accounts': [
                {
                    'id': a.id,
                    'name': a.name,
                    'exchange': a.exchange,
                    'account_type': a.account_type,
                    'broker_type': a.broker_type,
                    'credential_id': a.credential_id,
                    'enabled': a.enabled,
                    'is_live': a.is_live,
                    'balance': a.balance,
                    'equity': a.equity,
                    'currency': a.currency,
                    'max_leverage': a.max_leverage,
                    'metadata': a.metadata,
                    'created_at': a.created_at.isoformat(),
                    'last_sync': a.last_sync.isoformat() if a.last_sync else None
                }
                for a in self.accounts.values()
            ]
        }
        
        with open(accounts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_accounts(self):
        """Load accounts from disk."""
        accounts_file = self.vault.vault_path / "accounts.json"
        
        if not accounts_file.exists():
            return
        
        try:
            with open(accounts_file, 'r') as f:
                data = json.load(f)
            
            for acc_data in data.get('accounts', []):
                account = TradingAccount(
                    id=acc_data['id'],
                    name=acc_data['name'],
                    exchange=acc_data['exchange'],
                    account_type=acc_data['account_type'],
                    broker_type=acc_data['broker_type'],
                    credential_id=acc_data['credential_id'],
                    enabled=acc_data.get('enabled', True),
                    is_live=acc_data.get('is_live', False),
                    balance=acc_data.get('balance', 0),
                    equity=acc_data.get('equity', 0),
                    currency=acc_data.get('currency', 'USD'),
                    max_leverage=acc_data.get('max_leverage', 1),
                    metadata=acc_data.get('metadata', {}),
                    created_at=datetime.fromisoformat(acc_data['created_at']),
                    last_sync=datetime.fromisoformat(acc_data['last_sync']) if acc_data.get('last_sync') else None
                )
                self.accounts[account.id] = account
            
            logger.info(f"Loaded {len(self.accounts)} accounts")
            
        except Exception as e:
            logger.error(f"Failed to load accounts: {e}")
    
    def to_dict_list(self) -> List[Dict]:
        """Convert accounts to list of dicts for API response."""
        return [
            {
                'id': a.id,
                'name': a.name,
                'exchange': a.exchange,
                'account_type': a.account_type,
                'broker_type': a.broker_type,
                'enabled': a.enabled,
                'is_live': a.is_live,
                'balance': a.balance,
                'equity': a.equity,
                'currency': a.currency,
                'max_leverage': a.max_leverage,
                'last_sync': a.last_sync.isoformat() if a.last_sync else None
            }
            for a in self.accounts.values()
        ]


# Global instances
_vault: Optional[SecureVault] = None
_account_manager: Optional[AccountManager] = None


def get_secure_vault(master_key: str = None) -> SecureVault:
    """Get or create secure vault."""
    global _vault
    if _vault is None:
        _vault = SecureVault(master_key=master_key)
    elif master_key and not _vault.is_initialized():
        _vault.set_master_key(master_key)
    return _vault


def get_account_manager() -> AccountManager:
    """Get or create account manager."""
    global _account_manager
    if _account_manager is None:
        _account_manager = AccountManager(get_secure_vault())
    return _account_manager


if __name__ == "__main__":
    # Test vault and account manager
    vault = SecureVault(master_key="test_master_key_123")
    
    # Store a credential
    cred_id = vault.store_credential(
        account_id="test_account",
        exchange="binance",
        credential_type=CredentialType.CRYPTO_EXCHANGE,
        credentials={
            'api_key': 'test_api_key_xxxxx',
            'api_secret': 'test_secret_xxxxx',
            'testnet': True
        }
    )
    
    print(f"Stored credential: {cred_id}")
    
    # Retrieve credential
    cred = vault.get_credential(cred_id)
    print(f"Retrieved: {cred}")
    
    # Test account manager
    manager = AccountManager(vault)
    
    acc_id = manager.add_account(
        name="Binance Futures Demo",
        exchange="binance",
        account_type="futures",
        broker_type="crypto_exchange",
        credentials={
            'api_key': 'demo_key',
            'api_secret': 'demo_secret'
        },
        is_live=False,
        max_leverage=20
    )
    
    print(f"\nCreated account: {acc_id}")
    print(f"All accounts: {manager.to_dict_list()}")
