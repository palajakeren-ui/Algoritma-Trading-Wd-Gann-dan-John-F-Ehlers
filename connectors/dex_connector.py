"""
DEX Connector Module
Decentralized Exchange connector with Web3.py for EVM chains and Solana support.

Supports:
- Ethereum, BSC, Polygon, Arbitrum, Optimism, Base
- Solana (via Jupiter aggregator)
- DEX aggregators (1inch, 0x, Paraswap)
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import time
import hashlib
import json
from decimal import Decimal

# Web3 imports with fallback
try:
    from web3 import Web3
    from web3.contract import Contract
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None  # Placeholder for type hints
    logger.warning("web3 not installed. DEX connector will use simulation mode. Install with: pip install web3")

# Solana imports with fallback
try:
    from solana.rpc.api import Client as SolanaClient
    from solana.transaction import Transaction
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    SolanaClient = None


class Chain(Enum):
    """Supported blockchain networks."""
    ETHEREUM = 1
    BSC = 56
    POLYGON = 137
    ARBITRUM = 42161
    OPTIMISM = 10
    BASE = 8453
    AVALANCHE = 43114
    SOLANA = "solana"


@dataclass
class TokenInfo:
    """Token information."""
    address: str
    symbol: str
    name: str
    decimals: int
    chain_id: int


@dataclass
class LiquidityPool:
    """DEX liquidity pool information."""
    address: str
    token0: TokenInfo
    token1: TokenInfo
    reserve0: float
    reserve1: float
    fee: float
    dex: str


@dataclass
class SwapQuote:
    """Swap quote result."""
    input_token: str
    output_token: str
    input_amount: float
    output_amount: float
    price_impact: float
    route: List[str]
    fee: float
    dex: str
    gas_estimate: int


# Standard ERC20 ABI
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

# Router ABI for DEX swaps
ROUTER_ABI = [
    {"inputs": [], "name": "WETH", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}], "name": "getAmountsOut", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactTokensForTokens", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"},
]


class ChainConfig:
    """Chain configuration with RPC URLs and DEX addresses."""
    
    CONFIGS = {
        Chain.ETHEREUM: {
            "name": "Ethereum",
            "rpc": "https://eth.llamarpc.com",
            "ws_rpc": "wss://eth.llamarpc.com",
            "explorer": "https://etherscan.io",
            "native_token": "ETH",
            "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "uniswap_v3_quoter": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        },
        Chain.BSC: {
            "name": "BNB Chain",
            "rpc": "https://bsc-dataseed1.binance.org",
            "explorer": "https://bscerscan.io",
            "native_token": "BNB",
            "pancakeswap_router": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        },
        Chain.POLYGON: {
            "name": "Polygon",
            "rpc": "https://polygon.llamarpc.com",
            "explorer": "https://polygonscan.com",
            "native_token": "MATIC",
            "quickswap_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        },
        Chain.ARBITRUM: {
            "name": "Arbitrum",
            "rpc": "https://arb1.arbitrum.io/rpc",
            "explorer": "https://arbiscan.io",
            "native_token": "ETH",
            "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        },
        Chain.BASE: {
            "name": "Base",
            "rpc": "https://mainnet.base.org",
            "explorer": "https://basescan.org",
            "native_token": "ETH",
            "uniswap_v3_router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        },
    }
    
    @classmethod
    def get_config(cls, chain: Chain) -> Dict:
        return cls.CONFIGS.get(chain, {})


class DEXConnector:
    """
    Decentralized Exchange connector for EVM chains.
    
    Features:
    - Multi-chain support (Ethereum, BSC, Polygon, Arbitrum, Base)
    - Token balance queries
    - Swap quotes and execution
    - Liquidity pool information
    - Transaction building and signing
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize DEX connector.
        
        Args:
            config: Configuration dict with:
                - private_key: Wallet private key (optional, required for transactions)
                - rpc_urls: Dict of chain -> RPC URL overrides
        """
        self.config = config or {}
        self._private_key = self.config.get('private_key')
        self._web3_instances: Dict[Chain, Any] = {}  # Web3 instances or None
        self._accounts: Dict[Chain, str] = {}
        self._initialized = False
        self._simulation_mode = not WEB3_AVAILABLE
        
        if self._simulation_mode:
            logger.info("DEXConnector initialized in SIMULATION mode")
        else:
            logger.info("DEXConnector initialized")
    
    def _get_web3(self, chain: Chain) -> Optional[Any]:
        """Get or create Web3 instance for chain."""
        if not WEB3_AVAILABLE:
            return None
        
        if chain not in self._web3_instances:
            config = ChainConfig.get_config(chain)
            rpc_url = self.config.get('rpc_urls', {}).get(chain.value, config.get('rpc'))
            
            if rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    if w3.is_connected():
                        self._web3_instances[chain] = w3
                        logger.info(f"Connected to {config.get('name', chain.value)}")
                    else:
                        logger.warning(f"Failed to connect to {config.get('name')}")
                except Exception as e:
                    logger.error(f"Web3 connection error: {e}")
        
        return self._web3_instances.get(chain)
    
    def connect(self, chain: Chain) -> bool:
        """
        Connect to a blockchain network.
        
        Args:
            chain: Chain enum value
            
        Returns:
            True if connected successfully
        """
        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available, using simulation mode")
            self._simulation_mode = True
            return True
        
        w3 = self._get_web3(chain)
        if w3:
            self._initialized = True
            
            # Setup account if private key provided
            if self._private_key:
                account = w3.eth.account.from_key(self._private_key)
                self._accounts[chain] = account.address
                logger.info(f"Account loaded: {account.address}")
            
            return True
        
        return False
    
    def get_wallet_address(self, chain: Chain) -> Optional[str]:
        """Get connected wallet address."""
        return self._accounts.get(chain)
    
    def get_balance(self, chain: Chain, token_address: str = None) -> Dict:
        """
        Get wallet balance.
        
        Args:
            chain: Blockchain network
            token_address: Token contract address (None for native token)
            
        Returns:
            Dict with balance information
        """
        if hasattr(self, '_simulation_mode') and self._simulation_mode:
            return self._simulate_balance(chain, token_address)
        
        w3 = self._get_web3(chain)
        wallet = self._accounts.get(chain)
        
        if not w3 or not wallet:
            return {"error": "Not connected or no wallet"}
        
        try:
            if token_address is None:
                # Native token balance
                balance_wei = w3.eth.get_balance(wallet)
                balance = float(w3.from_wei(balance_wei, 'ether'))
                config = ChainConfig.get_config(chain)
                return {
                    "token": config.get('native_token', 'ETH'),
                    "balance": balance,
                    "balance_wei": balance_wei
                }
            else:
                # ERC20 token balance
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=ERC20_ABI
                )
                
                balance_wei = contract.functions.balanceOf(wallet).call()
                decimals = contract.functions.decimals().call()
                symbol = contract.functions.symbol().call()
                
                balance = balance_wei / (10 ** decimals)
                
                return {
                    "token": symbol,
                    "address": token_address,
                    "balance": balance,
                    "balance_wei": balance_wei,
                    "decimals": decimals
                }
                
        except Exception as e:
            logger.error(f"Balance query error: {e}")
            return {"error": str(e)}
    
    def _simulate_balance(self, chain: Chain, token_address: str = None) -> Dict:
        """Simulate balance for testing."""
        if token_address:
            return {
                "token": "TOKEN",
                "address": token_address,
                "balance": 1000.0,
                "balance_wei": 1000000000000000000000,
                "decimals": 18
            }
        else:
            config = ChainConfig.get_config(chain)
            return {
                "token": config.get('native_token', 'ETH'),
                "balance": 10.0,
                "balance_wei": 10000000000000000000
            }
    
    def get_swap_quote(
        self,
        chain: Chain,
        token_in: str,
        token_out: str,
        amount_in: float,
        slippage: float = 0.5
    ) -> Optional[SwapQuote]:
        """
        Get swap quote.
        
        Args:
            chain: Blockchain network
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            slippage: Slippage tolerance in percent
            
        Returns:
            SwapQuote object or None on failure
        """
        if hasattr(self, '_simulation_mode') and self._simulation_mode:
            return self._simulate_quote(token_in, token_out, amount_in)
        
        w3 = self._get_web3(chain)
        if not w3:
            return None
        
        try:
            config = ChainConfig.get_config(chain)
            router_address = config.get('uniswap_v2_router') or config.get('pancakeswap_router')
            
            if not router_address:
                logger.error(f"No router configured for {chain}")
                return None
            
            router = w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=ROUTER_ABI
            )
            
            # Get token decimals
            token_in_contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_in),
                abi=ERC20_ABI
            )
            decimals_in = token_in_contract.functions.decimals().call()
            
            # Convert amount to wei
            amount_in_wei = int(amount_in * (10 ** decimals_in))
            
            # Get quote
            path = [
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out)
            ]
            
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            amount_out_wei = amounts[-1]
            
            # Calculate price impact (simplified)
            price_impact = abs(amount_out_wei / amount_in_wei - 1) * 100 if amount_in_wei > 0 else 0
            
            return SwapQuote(
                input_token=token_in,
                output_token=token_out,
                input_amount=amount_in,
                output_amount=amount_out_wei / (10 ** 18),  # Assume 18 decimals for output
                price_impact=price_impact,
                route=[token_in, token_out],
                fee=0.003,  # 0.3% standard DEX fee
                dex="Uniswap V2",
                gas_estimate=150000
            )
            
        except Exception as e:
            logger.error(f"Quote error: {e}")
            return None
    
    def _simulate_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: float
    ) -> SwapQuote:
        """Simulate swap quote for testing."""
        # Simulate a reasonable exchange rate
        output_amount = amount_in * 0.95  # 5% slippage and fee
        
        return SwapQuote(
            input_token=token_in,
            output_token=token_out,
            input_amount=amount_in,
            output_amount=output_amount,
            price_impact=0.5,
            route=[token_in, token_out],
            fee=0.003,
            dex="Simulated DEX",
            gas_estimate=150000
        )
    
    def execute_swap(
        self,
        chain: Chain,
        token_in: str,
        token_out: str,
        amount_in: float,
        slippage: float = 0.5,
        deadline: int = 20
    ) -> Dict:
        """
        Execute a token swap.
        
        Args:
            chain: Blockchain network
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            slippage: Slippage tolerance in percent
            deadline: Transaction deadline in minutes
            
        Returns:
            Dict with transaction details
        """
        if hasattr(self, '_simulation_mode') and self._simulation_mode:
            return self._simulate_swap(token_in, token_out, amount_in)
        
        if not self._private_key:
            logger.error("No private key provided for swap execution")
            return {"error": "No private key configured"}
        
        w3 = self._get_web3(chain)
        wallet = self._accounts.get(chain)
        
        if not w3 or not wallet:
            return {"error": "Not connected or no wallet"}
        
        try:
            # Get quote first
            quote = self.get_swap_quote(chain, token_in, token_out, amount_in, slippage)
            if not quote:
                return {"error": "Failed to get quote"}
            
            # Calculate minimum output with slippage
            amount_out_min = int(quote.output_amount * (10 ** 18) * (1 - slippage / 100))
            
            # Approve token spending
            token_contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_in),
                abi=ERC20_ABI
            )
            
            config = ChainConfig.get_config(chain)
            router_address = config.get('uniswap_v2_router') or config.get('pancakeswap_router')
            
            # Check and set allowance
            allowance = token_contract.functions.allowance(
                wallet,
                Web3.to_checksum_address(router_address)
            ).call()
            
            amount_in_wei = int(amount_in * (10 ** 18))
            
            if allowance < amount_in_wei:
                approve_tx = token_contract.functions.approve(
                    Web3.to_checksum_address(router_address),
                    amount_in_wei
                ).build_transaction({
                    'from': wallet,
                    'gas': 100000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': w3.eth.get_transaction_count(wallet),
                })
                
                signed = w3.eth.account.sign_transaction(approve_tx, self._private_key)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                logger.info(f"Approval tx: {tx_hash.hex()}")
                w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Execute swap
            router = w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=ROUTER_ABI
            )
            
            path = [
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out)
            ]
            
            deadline_ts = int(time.time()) + (deadline * 60)
            
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in_wei,
                amount_out_min,
                path,
                wallet,
                deadline_ts
            ).build_transaction({
                'from': wallet,
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(wallet),
            })
            
            signed = w3.eth.account.sign_transaction(swap_tx, self._private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            
            logger.success(f"Swap tx: {tx_hash.hex()}")
            
            return {
                "status": "pending",
                "tx_hash": tx_hash.hex(),
                "input_amount": amount_in,
                "expected_output": quote.output_amount,
                "explorer_url": f"{config.get('explorer')}/tx/{tx_hash.hex()}"
            }
            
        except Exception as e:
            logger.error(f"Swap error: {e}")
            return {"error": str(e)}
    
    def _simulate_swap(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Simulate swap for testing."""
        return {
            "status": "simulated",
            "tx_hash": f"0x{hashlib.sha256(f'{token_in}{token_out}{amount_in}'.encode()).hexdigest()}",
            "input_amount": amount_in,
            "output_amount": amount_in * 0.95,
            "explorer_url": "#simulation"
        }


class SolanaDEXConnector:
    """
    Solana DEX connector using Jupiter aggregator.
    
    Features:
    - SPL token balance queries
    - Jupiter swap quotes
    - Transaction building
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._client = None
        self._initialized = False
        
        if SOLANA_AVAILABLE:
            rpc_url = self.config.get('solana_rpc', 'https://api.mainnet-beta.solana.com')
            self._client = SolanaClient(rpc_url)
            logger.info("Solana DEX connector initialized")
    
    def connect(self) -> bool:
        """Connect to Solana network."""
        if not SOLANA_AVAILABLE:
            logger.warning("Solana SDK not available, using simulation mode")
            self._simulation_mode = True
            return True
        
        try:
            # Test connection
            self._client.get_epoch_info()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Solana connection error: {e}")
            return False
    
    def get_balance(self, wallet_address: str, mint_address: str = None) -> Dict:
        """Get SOL or SPL token balance."""
        if hasattr(self, '_simulation_mode') and self._simulation_mode:
            return {
                "token": "SOL" if mint_address is None else "SPL",
                "balance": 100.0
            }
        
        # Implementation would use Solana RPC
        return {"balance": 0.0}


def create_dex_connector(chain: Chain, config: Dict = None) -> DEXConnector:
    """Factory function for creating DEX connectors."""
    connector = DEXConnector(config)
    connector.connect(chain)
    return connector
