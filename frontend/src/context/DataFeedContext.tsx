import React, { createContext, useContext, useRef, useCallback, useEffect, useMemo } from 'react';
import { io, Socket } from 'socket.io-client';

// ============================================================================
// TYPES - Pre-defined for zero allocation
// ============================================================================

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'http://localhost:5000';

export interface CandleData {
    time: string;
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    symbol: string;
}

export interface MarketData {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    open: number;
    high: number;
    low: number;
    volume: number;
    timestamp: number;  // Use number for better performance
    source: string;
}

interface DataFeedContextType {
    marketData: Record<string, MarketData>;
    candles: Record<string, CandleData[]>;
    isConnected: boolean;
    isKillSwitchActive: boolean;
    subscribe: (symbol: string) => void;
    unsubscribe: (symbol: string) => void;
}

// ============================================================================
// BATCH UPDATE SYSTEM - Prevents React re-render storms
// ============================================================================

const BATCH_INTERVAL_MS = 16; // ~60fps max update rate
const MAX_CANDLES_PER_SYMBOL = 100;

const DataFeedContext = createContext<DataFeedContextType | undefined>(undefined);

// Pre-allocated empty objects for initial state
const EMPTY_MARKET_DATA: Record<string, MarketData> = {};
const EMPTY_CANDLES: Record<string, CandleData[]> = {};

export const DataFeedProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    // Use refs for high-frequency updates (bypasses React re-renders)
    const marketDataRef = useRef<Record<string, MarketData>>({});
    const candlesRef = useRef<Record<string, CandleData[]>>({});
    const subscriptionsRef = useRef<Set<string>>(new Set());
    const pendingUpdatesRef = useRef<Map<string, MarketData>>(new Map());
    
    // State for React components (updated in batches)
    const [marketData, setMarketData] = React.useState<Record<string, MarketData>>(EMPTY_MARKET_DATA);
    const [candles, setCandles] = React.useState<Record<string, CandleData[]>>(EMPTY_CANDLES);
    const [isConnected, setIsConnected] = React.useState(false);
    const [isKillSwitchActive, setIsKillSwitchActive] = React.useState(false);
    
    const socketRef = useRef<Socket | null>(null);
    const batchTimerRef = useRef<NodeJS.Timeout | null>(null);

    // ============================================================================
    // BATCH UPDATE PROCESSOR - Runs at 60fps max
    // ============================================================================

    const processBatchUpdates = useCallback(() => {
        const pending = pendingUpdatesRef.current;
        if (pending.size === 0) return;

        // Batch update marketData
        const updates = Object.fromEntries(pending);
        pendingUpdatesRef.current.clear();

        setMarketData(prev => {
            const newState = { ...prev };
            for (const [symbol, data] of Object.entries(updates)) {
                newState[symbol] = data;
                marketDataRef.current[symbol] = data;
            }
            return newState;
        });

        // Batch update candles
        setCandles(prev => {
            const newState = { ...prev };
            for (const [symbol, data] of Object.entries(updates)) {
                const mData = data as MarketData;
                const existing = newState[symbol] || [];
                
                const newCandle: CandleData = {
                    time: new Date(mData.timestamp).toLocaleTimeString(),
                    date: new Date(mData.timestamp).toLocaleDateString(),
                    open: mData.open,
                    high: mData.high,
                    low: mData.low,
                    close: mData.price,
                    volume: mData.volume,
                    symbol
                };

                // Use last candle check for deduplication
                const lastCandle = existing[existing.length - 1];
                if (!lastCandle || lastCandle.time !== newCandle.time) {
                    newState[symbol] = [...existing, newCandle].slice(-MAX_CANDLES_PER_SYMBOL);
                } else {
                    // Update last candle
                    newState[symbol] = [...existing.slice(0, -1), newCandle];
                }
                candlesRef.current[symbol] = newState[symbol];
            }
            return newState;
        });
    }, []);

    // ============================================================================
    // SOCKET CONNECTION - Single connection, re-used subscriptions
    // ============================================================================

    useEffect(() => {
        const socket = io(WS_BASE_URL, {
            path: '/socket.io',
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[DataFeed] Connected to real-time feed');
            setIsConnected(true);
            
            // Re-subscribe to all active symbols
            subscriptionsRef.current.forEach(symbol => {
                socket.emit('subscribe', { symbol });
            });
        });

        socket.on('disconnect', () => {
            console.log('[DataFeed] Disconnected');
            setIsConnected(false);
        });

        // ============================================================================
        // PRICE UPDATE HANDLER - Queues updates for batch processing
        // ============================================================================

        socket.on('price_update', (data: any) => {
            const symbol = data.symbol;
            
            const mData: MarketData = {
                symbol,
                price: data.price,
                change: data.change,
                changePercent: data.changePercent,
                open: data.open,
                high: data.high,
                low: data.low,
                volume: data.volume,
                timestamp: data.timestamp || Date.now(),
                source: data.source || 'broker'
            };

            // Queue update for batch processing
            pendingUpdatesRef.current.set(symbol, mData);
        });

        // Start batch processor
        batchTimerRef.current = setInterval(processBatchUpdates, BATCH_INTERVAL_MS);

        return () => {
            if (batchTimerRef.current) {
                clearInterval(batchTimerRef.current);
            }
            socket.disconnect();
        };
    }, [processBatchUpdates]);

    // ============================================================================
    // SUBSCRIPTION MANAGEMENT - Deduplicated
    // ============================================================================

    const subscribe = useCallback((symbol: string) => {
        if (!subscriptionsRef.current.has(symbol)) {
            subscriptionsRef.current.add(symbol);
            if (socketRef.current?.connected) {
                socketRef.current.emit('subscribe', { symbol });
            }
        }
    }, []);

    const unsubscribe = useCallback((symbol: string) => {
        subscriptionsRef.current.delete(symbol);
    }, []);

    // Memoize context value to prevent unnecessary re-renders
    const contextValue = useMemo<DataFeedContextType>(() => ({
        marketData,
        candles,
        isConnected,
        isKillSwitchActive,
        subscribe,
        unsubscribe,
    }), [marketData, candles, isConnected, isKillSwitchActive, subscribe, unsubscribe]);

    return (
        <DataFeedContext.Provider value={contextValue}>
            {children}
        </DataFeedContext.Provider>
    );
};

// ============================================================================
// CUSTOM HOOK - Optimized selector
// ============================================================================

export const useDataFeed = () => {
    const context = useContext(DataFeedContext);
    if (context === undefined) {
        throw new Error('useDataFeed must be used within a DataFeedProvider');
    }
    return context;
};

// Selector hook for single symbol (prevents re-renders for other symbols)
export const useMarketData = (symbol: string): MarketData | undefined => {
    const { marketData } = useDataFeed();
    return marketData[symbol];
};

// Selector hook for candles
export const useCandles = (symbol: string): CandleData[] => {
    const { candles } = useDataFeed();
    return candles[symbol] || [];
};
