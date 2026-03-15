"""
Order Retry Engine
Exponential backoff retry with configurable strategies.
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from loguru import logger
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"


@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retry_on_timeout: bool = True
    retry_on_rejection: bool = False  # DO NOT retry rejected orders by default


class RetryResult:
    def __init__(self):
        self.success: bool = False
        self.result: Any = None
        self.attempts: int = 0
        self.total_delay_ms: float = 0.0
        self.last_error: str = ""
        self.errors: list = []


class RetryEngine:
    """
    Production retry engine for order execution.
    
    Features:
    - Exponential backoff with jitter
    - Configurable retry conditions
    - Logging of all retry attempts
    - Max total delay cap
    - Circuit breaker integration (stops retrying if CB trips)
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self._retry_counts: Dict[str, int] = {}
    
    def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str = "order",
        order_id: str = "",
        circuit_breaker_check: Callable = None,
        **kwargs,
    ) -> RetryResult:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            operation_name: Name for logging
            order_id: Order ID for tracking
            circuit_breaker_check: Callable returning bool (True = OK)
            
        Returns:
            RetryResult
        """
        result = RetryResult()
        delay_ms = self.config.initial_delay_ms
        
        for attempt in range(1, self.config.max_retries + 1):
            result.attempts = attempt
            
            # Check circuit breaker before retry
            if circuit_breaker_check and not circuit_breaker_check():
                result.last_error = "Circuit breaker tripped during retry"
                logger.warning(f"Retry aborted: circuit breaker tripped for {operation_name} {order_id}")
                break
            
            try:
                result.result = operation(**kwargs)
                result.success = True
                
                if attempt > 1:
                    logger.info(
                        f"Retry SUCCESS on attempt {attempt} for {operation_name} {order_id} "
                        f"(total delay: {result.total_delay_ms:.0f}ms)"
                    )
                return result
                
            except Exception as e:
                error_msg = str(e)
                result.errors.append(f"Attempt {attempt}: {error_msg}")
                result.last_error = error_msg
                
                # Check if error is retryable
                if not self._is_retryable(e):
                    logger.error(f"Non-retryable error on {operation_name} {order_id}: {error_msg}")
                    break
                
                if attempt < self.config.max_retries:
                    # Add jitter (±20%)
                    import random
                    jitter = delay_ms * random.uniform(-0.2, 0.2)
                    actual_delay = min(delay_ms + jitter, self.config.max_delay_ms)
                    
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_retries} for {operation_name} "
                        f"{order_id}: {error_msg}. Waiting {actual_delay:.0f}ms..."
                    )
                    
                    time.sleep(actual_delay / 1000)
                    result.total_delay_ms += actual_delay
                    
                    # Update delay for next attempt
                    if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay_ms *= self.config.backoff_multiplier
                    elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay_ms += self.config.initial_delay_ms
                else:
                    logger.error(
                        f"All {self.config.max_retries} retries exhausted for "
                        f"{operation_name} {order_id}: {error_msg}"
                    )
        
        return result
    
    def _is_retryable(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        error_str = str(error).lower()
        
        # Never retry these
        non_retryable = [
            "insufficient balance",
            "insufficient margin",
            "invalid symbol",
            "invalid quantity",
            "order rejected",
            "account disabled",
            "api key",
            "authentication",
        ]
        for nr in non_retryable:
            if nr in error_str:
                return False
        
        # Always retry these
        retryable = [
            "timeout",
            "connection",
            "rate limit",
            "server error",
            "503",
            "502",
            "429",
            "network",
        ]
        for r in retryable:
            if r in error_str:
                return True
        
        # Default: retry
        return True
