// ============================================================================
// TRADE HISTORY COMPONENT — Live Trading UI
// ============================================================================

import React, { memo, useMemo, useState, useCallback } from 'react';

// Types
interface Trade {
  id: number;
  clientOrderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  commission: number;
  pnl: number;
  timestamp: number;
}

interface TradeHistoryProps {
  trades?: Trade[];
  pageSize?: number;
  onExport?: () => void;
}

// Format timestamp
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp / 1_000_000); // Convert nanos to millis
  return date.toLocaleString();
};

// Format currency
const formatCurrency = (value: number): string => {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// Memoized Trade Row
const TradeRow: React.FC<{ trade: Trade }> = memo(({ trade }) => {
  const sideColor = trade.side === 'BUY' ? 'text-green-500' : 'text-red-500';
  const pnlColor = trade.pnl >= 0 ? 'text-green-500' : 'text-red-500';
  
  return (
    <tr className="border-b border-gray-700 hover:bg-gray-800">
      <td className="px-4 py-3 text-sm">{formatTime(trade.timestamp)}</td>
      <td className="px-4 py-3">
        <span className="font-medium">{trade.symbol}</span>
      </td>
      <td className="px-4 py-3">
        <span className={`${sideColor} font-medium`}>{trade.side}</span>
      </td>
      <td className="px-4 py-3 text-right">{trade.quantity}</td>
      <td className="px-4 py-3 text-right">${formatCurrency(trade.price)}</td>
      <td className="px-4 py-3 text-right text-gray-400">
        ${formatCurrency(trade.commission)}
      </td>
      <td className="px-4 py-3 text-right">
        <span className={`${pnlColor} font-medium`}>
          {trade.pnl >= 0 ? '+' : ''}${formatCurrency(trade.pnl)}
        </span>
      </td>
    </tr>
  );
});

TradeRow.displayName = 'TradeRow';

// Main Trade History Component
export const TradeHistory: React.FC<TradeHistoryProps> = memo(({
  trades: externalTrades,
  pageSize = 20,
  onExport,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [dateRange, setDateRange] = useState<'TODAY' | 'WEEK' | 'MONTH' | 'ALL'>('ALL');
  
  // Mock trades - in production, fetch from API
  const trades: Trade[] = useMemo(() => {
    return externalTrades || [];
  }, [externalTrades]);
  
  // Filtered trades
  const filteredTrades = useMemo(() => {
    let filtered = trades;
    
    // Side filter
    if (filter !== 'ALL') {
      filtered = filtered.filter(t => t.side === filter);
    }
    
    // Date filter
    const now = Date.now();
    if (dateRange === 'TODAY') {
      const todayStart = new Date().setHours(0, 0, 0, 0) * 1_000_000;
      filtered = filtered.filter(t => t.timestamp >= todayStart);
    } else if (dateRange === 'WEEK') {
      const weekAgo = (now - 7 * 24 * 60 * 60 * 1000) * 1_000_000;
      filtered = filtered.filter(t => t.timestamp >= weekAgo);
    } else if (dateRange === 'MONTH') {
      const monthAgo = (now - 30 * 24 * 60 * 60 * 1000) * 1_000_000;
      filtered = filtered.filter(t => t.timestamp >= monthAgo);
    }
    
    return filtered;
  }, [trades, filter, dateRange]);
  
  // Pagination
  const totalPages = Math.ceil(filteredTrades.length / pageSize);
  const paginatedTrades = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredTrades.slice(start, start + pageSize);
  }, [filteredTrades, currentPage, pageSize]);
  
  // Summary stats
  const stats = useMemo(() => {
    const totalPnL = filteredTrades.reduce((sum, t) => sum + t.pnl, 0);
    const totalCommission = filteredTrades.reduce((sum, t) => sum + t.commission, 0);
    const winCount = filteredTrades.filter(t => t.pnl > 0).length;
    const lossCount = filteredTrades.filter(t => t.pnl < 0).length;
    const winRate = filteredTrades.length > 0 ? (winCount / filteredTrades.length) * 100 : 0;
    
    return { totalPnL, totalCommission, winCount, lossCount, winRate };
  }, [filteredTrades]);
  
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);
  
  return (
    <div className="h-full flex flex-col bg-card rounded-lg">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Trade History</h2>
          {onExport && (
            <button
              onClick={onExport}
              className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 rounded"
            >
              Export CSV
            </button>
          )}
        </div>
        
        {/* Filters */}
        <div className="flex gap-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as 'ALL' | 'BUY' | 'SELL')}
            className="px-3 py-1 bg-gray-800 border rounded text-sm"
          >
            <option value="ALL">All Sides</option>
            <option value="BUY">Buy Only</option>
            <option value="SELL">Sell Only</option>
          </select>
          
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as 'TODAY' | 'WEEK' | 'MONTH' | 'ALL')}
            className="px-3 py-1 bg-gray-800 border rounded text-sm"
          >
            <option value="ALL">All Time</option>
            <option value="TODAY">Today</option>
            <option value="WEEK">Last 7 Days</option>
            <option value="MONTH">Last 30 Days</option>
          </select>
        </div>
      </div>
      
      {/* Stats Summary */}
      <div className="p-4 border-b bg-gray-800">
        <div className="grid grid-cols-5 gap-4 text-center">
          <div>
            <div className="text-gray-400 text-sm">Trades</div>
            <div className="font-bold">{filteredTrades.length}</div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">Win/Loss</div>
            <div className="font-bold">
              <span className="text-green-500">{stats.winCount}</span>
              <span className="text-gray-400">/</span>
              <span className="text-red-500">{stats.lossCount}</span>
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">Win Rate</div>
            <div className="font-bold">{stats.winRate.toFixed(1)}%</div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">Total P&L</div>
            <div className={`font-bold ${stats.totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              ${formatCurrency(stats.totalPnL)}
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">Commission</div>
            <div className="font-bold text-red-400">
              ${formatCurrency(stats.totalCommission)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="bg-gray-800 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Time</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Symbol</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Side</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Qty</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Price</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Comm</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">P&L</th>
            </tr>
          </thead>
          <tbody>
            {paginatedTrades.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-400">
                  No trades found
                </td>
              </tr>
            ) : (
              paginatedTrades.map((trade) => (
                <TradeRow key={trade.id} trade={trade} />
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t flex justify-center items-center gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-3 py-1 bg-gray-700 rounded disabled:opacity-50"
          >
            Prev
          </button>
          <span className="px-4">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="px-3 py-1 bg-gray-700 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
});

TradeHistory.displayName = 'TradeHistory';

export default TradeHistory;
