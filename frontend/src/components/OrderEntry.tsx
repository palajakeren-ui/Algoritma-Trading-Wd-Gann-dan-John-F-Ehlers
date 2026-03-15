// ============================================================================
// ORDER ENTRY COMPONENT — Live Trading UI
// ============================================================================

import React, { memo, useCallback, useState, useMemo } from 'react';
import { useDataFeed } from '@/context/DataFeedContext';

// Order types
enum OrderType {
  MARKET = 'MARKET',
  LIMIT = 'LIMIT',
  STOP_MARKET = 'STOP_MARKET',
  STOP_LIMIT = 'STOP_LIMIT',
}

// Order side
enum OrderSide {
  BUY = 'BUY',
  SELL = 'SELL',
}

// Time in force
enum TimeInForce {
  GTC = 'GTC',
  IOC = 'IOC',
  FOK = 'FOK',
  GTX = 'GTX', // Post-only
}

// Order request interface
interface OrderRequest {
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  price?: number;
  stop_price?: number;
  time_in_force: TimeInForce;
  idempotency_key: string;
}

// Order response interface
interface OrderResponse {
  success: boolean;
  client_order_id?: string;
  error?: string;
  reason?: string;
}

interface OrderEntryProps {
  symbol?: string;
  maxQuantity?: number;
  onOrderSubmit?: (order: OrderRequest) => void;
}

// Memoized Order Entry Component
export const OrderEntry: React.FC<OrderEntryProps> = memo(({
  symbol: defaultSymbol = 'BTCUSDT',
  maxQuantity = 10,
  onOrderSubmit,
}) => {
  const { isKillSwitchActive } = useDataFeed();
  
  // Form state - using individual state to prevent object recreation
  const [side, setSide] = useState<OrderSide>(OrderSide.BUY);
  const [orderType, setOrderType] = useState<OrderType>(OrderType.LIMIT);
  const [quantity, setQuantity] = useState<string>('0');
  const [price, setPrice] = useState<string>('');
  const [stopPrice, setStopPrice] = useState<string>('');
  const [timeInForce, setTimeInForce] = useState<TimeInForce>(TimeInForce.GTC);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Generate idempotency key
  const generateIdempotencyKey = useCallback(() => {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  }, []);
  
  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isKillSwitchActive) {
      setError('Trading is disabled - Kill switch is active');
      return;
    }
    
    if (!quantity || parseFloat(quantity) <= 0) {
      setError('Please enter a valid quantity');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const order: OrderRequest = {
      symbol,
      side,
      order_type: orderType,
      quantity: parseFloat(quantity),
      price: price ? parseFloat(price) : undefined,
      stop_price: stopPrice ? parseFloat(stopPrice) : undefined,
      time_in_force: timeInForce,
      idempotency_key: generateIdempotencyKey(),
    };
    
    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      });
      
      const result: OrderResponse = await response.json();
      
      if (result.success) {
        setQuantity('');
        setPrice('');
        setStopPrice('');
        onOrderSubmit?.(order);
      } else {
        setError(result.error || result.reason || 'Order submission failed');
      }
    } catch (err) {
      setError('Network error - please try again');
    } finally {
      setLoading(false);
    }
  }, [symbol, side, orderType, quantity, price, stopPrice, timeInForce, isKillSwitchActive, generateIdempotencyKey, onOrderSubmit]);
  
  // Memoized handlers
  const handleSideChange = useCallback((newSide: OrderSide) => setSide(newSide), []);
  const handleOrderTypeChange = useCallback((type: OrderType) => setOrderType(type), []);
  const handleQuantityChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuantity(e.target.value);
  }, []);
  const handlePriceChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setPrice(e.target.value);
  }, []);
  const handleStopPriceChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setStopPrice(e.target.value);
  }, []);
  const handleTIFChange = useCallback((tif: TimeInForce) => setTimeInForce(tif), []);
  
  // Calculate estimated value
  const estimatedValue = useMemo(() => {
    const qty = parseFloat(quantity) || 0;
    const prc = parseFloat(price) || 0;
    return qty * prc || 0;
  }, [quantity, price]);
  
  return (
    <div className="p-4 bg-card rounded-lg border">
      {/* Kill Switch Warning */}
      {isKillSwitchActive && (
        <div className="bg-red-500 text-white p-3 rounded-t-lg mb-4">
          <span className="font-bold">⚠ KILL SWITCH ACTIVE</span>
          <span className="text-sm">Trading is disabled</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Symbol and Side Selection */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              disabled
              className="w-full px-3 py-2 border rounded bg-gray-800"
            />
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Side</label>
            <select
              value={side}
              onChange={(e) => handleSideChange(e.target.value as OrderSide)}
              className="w-full px-3 py-2 border rounded"
              disabled={loading || isKillSwitchActive}
            >
              <option value={OrderSide.BUY}>Buy</option>
              <option value={OrderSide.SELL}>Sell</option>
            </select>
          </div>
        </div>
        
        {/* Order Type Selection */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Order Type</label>
            <select
              value={orderType}
              onChange={(e) => handleOrderTypeChange(e.target.value as OrderType)}
              className="w-full px-3 py-2 border rounded"
              disabled={loading || isKillSwitchActive}
            >
              <option value={OrderType.MARKET}>Market</option>
              <option value={OrderType.LIMIT}>Limit</option>
              <option value={OrderType.STOP_MARKET}>Stop Market</option>
              <option value={OrderType.STOP_LIMIT}>Stop Limit</option>
            </select>
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Quantity</label>
            <input
              type="number"
              value={quantity}
              onChange={handleQuantityChange}
              className="w-full px-3 py-2 border rounded"
              placeholder="0.00"
              disabled={loading || isKillSwitchActive}
              max={maxQuantity}
              step="any"
            />
          </div>
        </div>
        
        {/* Limit/Stop Price - only for certain order types */}
        {(orderType === OrderType.LIMIT || orderType === OrderType.STOP_LIMIT) && (
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">
                {orderType === OrderType.LIMIT ? 'Limit Price' : 'Stop Price'}
              </label>
              <input
                type="number"
                value={orderType === OrderType.LIMIT ? price : stopPrice}
                onChange={orderType === OrderType.LIMIT ? handlePriceChange : handleStopPriceChange}
                className="w-full px-3 py-2 border rounded"
                placeholder={orderType === OrderType.LIMIT ? '0.00' : '0.00'}
                disabled={loading || isKillSwitchActive}
                step="any"
              />
            </div>
          </div>
        )}
        
        {/* Time in Force */}
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Time in Force</label>
            <select
              value={timeInForce}
              onChange={(e) => handleTIFChange(e.target.value as TimeInForce)}
              className="w-full px-3 py-2 border rounded"
              disabled={loading || isKillSwitchActive}
            >
              <option value={TimeInForce.GTC}>Good Till Cancel</option>
              <option value={TimeInForce.IOC}>Immediate or Cancel</option>
              <option value={TimeInForce.FOK}>Fill or Kill</option>
              <option value={TimeInForce.GTX}>Post Only</option>
            </select>
          </div>
        </div>
        
        {/* Estimated Value */}
        {estimatedValue > 0 && (
          <div className="text-sm text-gray-500">
            Estimated Value: ${estimatedValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || isKillSwitchActive}
          className={`w-full py-2 px-4 rounded font-medium ${
            side === OrderSide.BUY 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-red-600 hover:bg-red-700'
          } text-white disabled:opacity-50`}
        >
          {loading ? 'Submitting...' : `${side} ${symbol}`}
        </button>
      </form>
    </div>
  );
});

OrderEntry.displayName = 'OrderEntry';

export default OrderEntry;
