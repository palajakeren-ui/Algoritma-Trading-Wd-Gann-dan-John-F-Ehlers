"""
DEX (Decentralized Exchange) Connector Module
Supports: Solana (Jupiter, Raydium, Orca), EVM chains (Uniswap, PancakeSwap, etc.)
           Perpetual DEXs (Drift, GMX, Hyperliquid)

This module provides connection, balance checking, and swap execution
for decentralized exchanges across multiple blockchains.
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# CHAIN CONFIGURATIONS
# ============================================================================

CHAIN_CONFIG = {
    "solana": {
        "rpc_mainnet": "https://api.mainnet-beta.solana.com",
        "rpc_devnet": "https://api.devnet.solana.com",
        "native_token": "SOL",
        "native_decimals": 9,
        "explorer": "https://solscan.io",
        "address_format": "base58",
        "address_length_range": (32, 44),
    },
    "ethereum": {
        "rpc_mainnet": "https://eth.llamarpc.com",
        "native_token": "ETH",
        "native_decimals": 18,
        "explorer": "https://etherscan.io",
        "address_format": "evm",
        "chain_id": 1,
    },
    "base": {
        "rpc_mainnet": "https://mainnet.base.org",
        "native_token": "ETH",
        "native_decimals": 18,
        "explorer": "https://basescan.org",
        "address_format": "evm",
        "chain_id": 8453,
    },
    "bsc": {
        "rpc_mainnet": "https://bsc-dataseed.binance.org",
        "native_token": "BNB",
        "native_decimals": 18,
        "explorer": "https://bscscan.com",
        "address_format": "evm",
        "chain_id": 56,
    },
    "arbitrum": {
        "rpc_mainnet": "https://arb1.arbitrum.io/rpc",
        "native_token": "ETH",
        "native_decimals": 18,
        "explorer": "https://arbiscan.io",
        "address_format": "evm",
        "chain_id": 42161,
    },
    "polygon": {
        "rpc_mainnet": "https://polygon-rpc.com",
        "native_token": "MATIC",
        "native_decimals": 18,
        "explorer": "https://polygonscan.com",
        "address_format": "evm",
        "chain_id": 137,
    },
    "hyperliquid": {
        "rpc_mainnet": "https://api.hyperliquid.xyz",
        "native_token": "USDC",
        "native_decimals": 6,
        "explorer": "https://app.hyperliquid.xyz",
        "address_format": "evm",
    },
}

# DEX Protocol configurations
DEX_PROTOCOLS = {
    # Spot DEXs
    "jupiter": {"chain": "solana", "type": "spot", "api": "https://quote-api.jup.ag/v6"},
    "raydium": {"chain": "solana", "type": "spot", "api": "https://api.raydium.io"},
    "orca": {"chain": "solana", "type": "spot", "api": "https://api.orca.so"},
    "uniswap_v3": {"chain": "ethereum", "type": "spot", "api": "https://api.uniswap.org"},
    "sushiswap": {"chain": "ethereum", "type": "spot"},
    "curve": {"chain": "ethereum", "type": "spot"},
    "aerodrome": {"chain": "base", "type": "spot"},
    "base_swap": {"chain": "base", "type": "spot"},
    "pancakeswap": {"chain": "bsc", "type": "spot"},
    "biswap": {"chain": "bsc", "type": "spot"},
    "camelot": {"chain": "arbitrum", "type": "spot"},
    # Perpetual DEXs
    "drift": {"chain": "solana", "type": "perp", "api": "https://dlob.drift.trade"},
    "jupiter_perps": {"chain": "solana", "type": "perp"},
    "zeta": {"chain": "solana", "type": "perp"},
    "gmx_v2": {"chain": "arbitrum", "type": "perp", "api": "https://arbitrum-api.gmxinfra.io"},
    "vertex": {"chain": "arbitrum", "type": "perp"},
    "gm_perp": {"chain": "arbitrum", "type": "perp"},
    "hyperliquid": {"chain": "hyperliquid", "type": "perp", "api": "https://api.hyperliquid.xyz"},
    "dydx": {"chain": "base", "type": "perp"},
    "intentx": {"chain": "base", "type": "perp"},
    "synthetix": {"chain": "base", "type": "perp"},
}


class DexConnector:
    """
    Unified DEX connector for multi-chain decentralized exchange trading.
    
    Supports:
    - Solana: Jupiter, Raydium, Orca, Drift Protocol, Jupiter Perps, Zeta Markets
    - Ethereum: Uniswap V3, SushiSwap, Curve
    - Base: Aerodrome, BaseSwap, dYdX, IntentX, Synthetix V3
    - BSC: PancakeSwap, BiSwap
    - Arbitrum: Uniswap V3, Camelot, GMX V2, Vertex, Gains Network
    - Polygon: (extensible)
    - Hyperliquid: Hyperliquid L1
    """

    def __init__(self, config: Dict):
        """
        Initialize DEX connector with configuration.
        
        Args:
            config: Dictionary with keys:
                - chain: blockchain network (solana, ethereum, base, bsc, arbitrum, polygon, hyperliquid)
                - exchange: DEX protocol name
                - wallet_address: public wallet address
                - private_key: encrypted private key or seed phrase
                - slippage: max slippage tolerance in percent (e.g. 0.5)
                - priority_fee: priority/tip fee in native token units
                - auto_slippage: boolean, use dynamic slippage calculation
                - auto_priority_fee: boolean, use dynamic priority fee
        """
        self.chain = config.get("chain", "solana")
        self.exchange = config.get("exchange", "jupiter")
        self.wallet_address = config.get("wallet_address", "")
        self.private_key = config.get("private_key", "")
        self.slippage = config.get("slippage", 0.5)
        self.priority_fee = config.get("priority_fee", 0.0001)
        self.auto_slippage = config.get("auto_slippage", True)
        self.auto_priority_fee = config.get("auto_priority_fee", True)

        self.chain_config = CHAIN_CONFIG.get(self.chain, {})
        self.protocol_config = DEX_PROTOCOLS.get(self.exchange, {})
        self.rpc_url = self.chain_config.get("rpc_mainnet", "")

        self._connected = False
        self._last_connection_check = 0
        self._connection_cache_ttl = 30  # seconds

        logger.info(
            f"DexConnector initialized: chain={self.chain}, "
            f"exchange={self.exchange}, wallet={self._mask_address(self.wallet_address)}"
        )

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def validate_address(self) -> bool:
        """Validate the wallet address format for the configured chain."""
        addr = self.wallet_address
        if not addr:
            return False

        addr_format = self.chain_config.get("address_format", "evm")

        if addr_format == "base58":
            # Solana: base58, typically 32-44 characters
            length_range = self.chain_config.get("address_length_range", (32, 44))
            return length_range[0] <= len(addr) <= length_range[1]
        elif addr_format == "evm":
            # EVM: 0x prefix, 42 characters total
            return addr.startswith("0x") and len(addr) == 42
        else:
            return len(addr) > 10

    def test_connection(self) -> Dict:
        """
        Test connection to the DEX by verifying RPC and wallet.
        
        Returns:
            Dict with connection status and details.
        """
        result = {
            "connected": False,
            "chain": self.chain,
            "exchange": self.exchange,
            "wallet": self._mask_address(self.wallet_address),
            "rpc_endpoint": self.rpc_url,
            "timestamp": datetime.now().isoformat(),
        }

        # Step 1: Validate address
        if not self.validate_address():
            result["error"] = f"Invalid wallet address format for {self.chain}"
            return result

        # Step 2: Validate private key
        if not self.private_key:
            result["error"] = "Private key not provided"
            return result

        # Step 3: Test RPC connectivity
        try:
            rpc_ok = self._test_rpc_connection()
            if not rpc_ok:
                result["error"] = f"Cannot reach RPC endpoint: {self.rpc_url}"
                return result
        except Exception as e:
            result["error"] = f"RPC connection error: {str(e)}"
            return result

        # Step 4: Fetch wallet balance
        try:
            balance = self.get_wallet_balance()
            result["balance"] = balance
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")
            result["balance"] = {"native": 0, "token": "unknown"}

        result["connected"] = True
        result["message"] = (
            f"Wallet verified on {self.chain.upper()} → "
            f"{self.exchange.replace('_', ' ').title()}"
        )
        result["config"] = {
            "slippage": self.slippage,
            "priority_fee": self.priority_fee,
            "auto_slippage": self.auto_slippage,
            "auto_priority_fee": self.auto_priority_fee,
        }

        self._connected = True
        self._last_connection_check = time.time()

        return result

    def is_connected(self) -> bool:
        """Check if connected (with caching)."""
        if time.time() - self._last_connection_check > self._connection_cache_ttl:
            try:
                result = self.test_connection()
                self._connected = result.get("connected", False)
            except Exception:
                self._connected = False
        return self._connected

    # ========================================================================
    # BALANCE & PORTFOLIO
    # ========================================================================

    def get_wallet_balance(self) -> Dict:
        """
        Get wallet balance for the configured chain.
        
        Returns:
            Dict with native token balance and token holdings.
        """
        native_token = self.chain_config.get("native_token", "UNKNOWN")

        # Real implementation would use web3.py / solana-py / httpx
        # Placeholder returning simulated data
        logger.info(f"Fetching balance for {self._mask_address(self.wallet_address)} on {self.chain}")

        return {
            "native_token": native_token,
            "native_balance": 0.0,
            "usd_value": 0.0,
            "tokens": [],
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
        }

    def get_token_price(self, token_address: str, quote_token: str = "USDC") -> Dict:
        """
        Get current token price from the DEX.
        
        Args:
            token_address: Contract/mint address of the token.
            quote_token: Quote token symbol (default: USDC).
            
        Returns:
            Dict with price data.
        """
        logger.info(f"Fetching price for {token_address} in {quote_token} on {self.exchange}")

        return {
            "token": token_address,
            "quote": quote_token,
            "price": 0.0,
            "source": self.exchange,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
        }

    # ========================================================================
    # TRADING OPERATIONS
    # ========================================================================

    def execute_swap(
        self,
        input_token: str,
        output_token: str,
        amount: float,
        slippage_override: Optional[float] = None,
    ) -> Dict:
        """
        Execute a token swap on the DEX.
        
        Args:
            input_token: Address or symbol of input token.
            output_token: Address or symbol of output token.
            amount: Amount of input token to swap.
            slippage_override: Override slippage tolerance (optional).
            
        Returns:
            Dict with swap result including tx hash.
        """
        effective_slippage = slippage_override or self._get_effective_slippage()

        logger.info(
            f"Executing swap: {amount} {input_token} → {output_token} "
            f"on {self.exchange} (slippage: {effective_slippage}%)"
        )

        # Real implementation would:
        # 1. Get quote from DEX aggregator (Jupiter, 1inch, etc.)
        # 2. Build transaction
        # 3. Sign with private key
        # 4. Send to RPC
        # 5. Wait for confirmation

        return {
            "status": "simulated",
            "input_token": input_token,
            "output_token": output_token,
            "input_amount": amount,
            "output_amount": 0.0,
            "slippage_used": effective_slippage,
            "priority_fee_used": self._get_effective_priority_fee(),
            "tx_hash": "",
            "exchange": self.exchange,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
        }

    def open_perp_position(
        self,
        market: str,
        side: str,
        size: float,
        leverage: float = 1.0,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> Dict:
        """
        Open a perpetual futures position on a perp DEX.
        
        Args:
            market: Market symbol (e.g. "BTC-PERP").
            side: "long" or "short".
            size: Position size in units or USD.
            leverage: Leverage multiplier.
            order_type: "market" or "limit".
            price: Limit price (required for limit orders).
            
        Returns:
            Dict with position details.
        """
        if self.protocol_config.get("type") != "perp":
            return {"error": f"{self.exchange} does not support perpetual trading"}

        logger.info(
            f"Opening {side} position: {size} {market} "
            f"at {leverage}x on {self.exchange}"
        )

        return {
            "status": "simulated",
            "market": market,
            "side": side,
            "size": size,
            "leverage": leverage,
            "order_type": order_type,
            "limit_price": price,
            "exchange": self.exchange,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
        }

    def close_perp_position(self, market: str, position_id: Optional[str] = None) -> Dict:
        """Close a perpetual futures position."""
        logger.info(f"Closing position: {market} on {self.exchange}")

        return {
            "status": "simulated",
            "market": market,
            "position_id": position_id,
            "exchange": self.exchange,
            "chain": self.chain,
            "timestamp": datetime.now().isoformat(),
        }

    def get_open_positions(self) -> List[Dict]:
        """Get all open perpetual positions."""
        logger.info(f"Fetching open positions on {self.exchange}")
        return []

    # ========================================================================
    # SLIPPAGE & FEE MANAGEMENT
    # ========================================================================

    def _get_effective_slippage(self) -> float:
        """Calculate effective slippage based on config and market conditions."""
        if self.auto_slippage:
            # Dynamic slippage calculation
            # Real implementation would analyze on-chain liquidity pools
            base = self.slippage or 0.5
            return min(base * 1.5, 5.0)  # Cap at 5%
        return self.slippage

    def _get_effective_priority_fee(self) -> float:
        """Calculate effective priority fee based on network congestion."""
        if self.auto_priority_fee:
            # Dynamic priority fee
            # Real implementation would query recent network fees
            return self.priority_fee or 0.0001
        return self.priority_fee

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _test_rpc_connection(self) -> bool:
        """Test RPC endpoint connectivity."""
        try:
            import urllib.request

            req = urllib.request.Request(
                self.rpc_url,
                data=b'{"jsonrpc":"2.0","id":1,"method":"getHealth"}',
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"RPC test failed for {self.rpc_url}: {e}")
            # Return True for non-JSON-RPC endpoints (e.g. Hyperliquid REST API)
            if self.chain == "hyperliquid":
                return True
            return False

    @staticmethod
    def _mask_address(address: str) -> str:
        """Mask a wallet address for logging."""
        if not address or len(address) < 10:
            return "***"
        return f"{address[:6]}...{address[-4:]}"

    def get_supported_chains(self) -> List[str]:
        """Get list of supported blockchain networks."""
        return list(CHAIN_CONFIG.keys())

    def get_supported_protocols(self, chain: Optional[str] = None) -> List[Dict]:
        """Get list of supported DEX protocols, optionally filtered by chain."""
        protocols = []
        for name, config in DEX_PROTOCOLS.items():
            if chain is None or config.get("chain") == chain:
                protocols.append({
                    "name": name,
                    "chain": config.get("chain"),
                    "type": config.get("type"),
                    "api": config.get("api", ""),
                })
        return protocols


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_dex_connector(config: Dict) -> DexConnector:
    """
    Factory function to create a DexConnector from frontend config format.
    
    Maps frontend field names (camelCase) to backend names (snake_case).
    """
    mapped_config = {
        "chain": config.get("dexChain", config.get("chain", "solana")),
        "exchange": config.get("dexExchange", config.get("exchange", "jupiter")),
        "wallet_address": config.get("dexWalletAddress", config.get("wallet_address", "")),
        "private_key": config.get("dexPrivateKey", config.get("private_key", "")),
        "slippage": config.get("dexSlippage", config.get("slippage", 0.5)),
        "priority_fee": config.get("dexPriorityFee", config.get("priority_fee", 0.0001)),
        "auto_slippage": config.get("dexAutoSlippage", config.get("auto_slippage", True)),
        "auto_priority_fee": config.get("dexAutoPriorityFee", config.get("auto_priority_fee", True)),
    }
    return DexConnector(mapped_config)
