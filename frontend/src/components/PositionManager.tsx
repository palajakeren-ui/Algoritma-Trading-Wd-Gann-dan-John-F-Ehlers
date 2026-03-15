// ============================================================================
// POSITION MANAGEMENT COMPONENT — Live Trading UI
// ============================================================================

import React, { memo, useMemo, useCallback } from 'react';
import { useDataFeed } from '@/context/DataFeedContext';

// Types
interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  pnlPercent: number;
  openedAt: number;
}

interface PositionManagerProps {
  onClosePosition?: (symbol: string) => void;
  maxPositions?: number;
}

// Memoized Position Card
const PositionCard: React.FC<{
  position: Position;
  onClose: () => void;
  isKillSwitchActive: boolean;
}> = memo(({ position, onClose, isKillSwitchActive }) => {
  const pnlColor = position.unrealizedPnl >= 0 ? 'text-green-500' : 'text-red-500';
  const sideColor = position.side === 'LONG' ? 'bg-green-500' : 'bg-red-500';
  
  const formatPrice = useCallback((price: number) => {
    return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, []);
  
  const formatPnL = useCallback((pnl: number) => {
    const sign = pnl >= 0 ? '+' : '';
    return `${sign}$${Math.abs(pnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  }, []);
  
  return (
    <div className="bg-card border rounded-lg p-4 mb-3">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className={`${sideColor} text-white text-xs px-2 py-1 rounded`}>
            {position.side}
          </span>
          <span className="font-bold text-lg">{position.symbol}</span>
        </div>
        <button
          onClick={onClose}
          disabled={isKillSwitchActive}
          className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50"
        >
          Close
        </button>
      </div>
      
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-400">Quantity</span>
          <div className="font-medium">{position.quantity}</div>
        </div>
        <div>
          <span className="text-gray-400">Entry</span>
          <div className="font-medium">${formatPrice(position.entryPrice)}</div>
        </div>
        <div>
          <span className="text-gray-400">Current</span>
          <div className="font-medium">${formatPrice(position.currentPrice)}</div>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t flex justify-between items-center">
        <span className="text-gray-400">Unrealized P&L</span>
        <span className={`font-bold text-lg ${pnlColor}`}>
          {formatPnL(position.unrealizedPnl)}
          <span className="text-sm ml-1">({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%)</span>
        </span>
      </div>
    </div>
  );
});

PositionCard.displayName = 'PositionCard';

// Main Position Manager Component
export const PositionManager: React.FC<PositionManagerProps> = memo(({
  onClosePosition,
  maxPositions = 10,
}) => {
  const { portfolio, isKillSwitchActive } = useDataFeed();
  
  // Mock positions - in production, this would come from WebSocket
  const positions: Position[] = useMemo(() => {
    // This would be populated from the data feed
    return [];
  }, []);
  
  const totalUnrealizedPnL = useMemo(() => {
    return positions.reduce((sum, p) => sum + p.unrealizedPnL, 0);
  }, [positions]);
  
  const handleClosePosition = useCallback((symbol: string) => {
    if (isKillSwitchActive) return;
    onClosePosition?.(symbol);
  }, [isKillSwitchActive, onClosePosition]);
  
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-card">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">Positions</h2>
          <span className="text-sm text-gray-400">
            {positions.length} / {maxPositions}
          </span>
        </div>
        
        {/* Summary */}
        <div className="mt-3 grid grid-cols-3 gap-4">
          <div>
            <span className="text-gray-400 text-sm">Total Value</span>
            <div className="font-bold">
              ${portfolio?.equity?.toLocaleString() || '0'}
            </div>
          </div>
          <div>
            <span className="text-gray-400 text-sm">Unrealized P&L</span>
            <div className={`font-bold ${totalUnrealizedPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {totalUnrealizedPnL >= 0 ? '+' : ''}${Math.abs(totalUnrealizedPnL).toLocaleString()}
            </div>
          </div>
          <div>
            <span className="text-gray-400 text-sm">Drawdown</span>
            <div className="font-bold text-red-400">
              {portfolio?.drawdown_bps ? (portfolio.drawdown_bps / 100).toFixed(2) : '0.00'}%
            </div>
          </div>
        </div>
      </div>
      
      {/* Positions List */}
      <div className="flex-1 overflow-y-auto p-4">
        {isKillSwitchActive && (
          <div className="bg-red-500 text-white p-3 rounded mb-4">
            ⚠️ Trading Disabled - Kill Switch Active
          </div>
        )}
        
        {positions.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No open positions
          </div>
        ) : (
          positions.map((position) => (
            <PositionCard
              key={position.symbol}
              position={position}
              onClose={() => handleClosePosition(position.symbol)}
              isKillSwitchActive={isKillSwitchActive}
            />
          ))
        )}
      </div>
      
      {/* Footer Actions */}
      <div className="p-4 border-t bg-card">
        <button
          disabled={isKillSwitchActive || positions.length === 0}
          className="w-full py-2 bg-red-600 hover:bg-red-700 text-white rounded disabled:opacity-50"
        >
          Close All Positions
        </button>
      </div>
    </div>
  );
});

PositionManager.displayName = 'PositionManager';

export default PositionManager;
