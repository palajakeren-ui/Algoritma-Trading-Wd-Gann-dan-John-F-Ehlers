import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

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
    timestamp: Date;
    source: string;
}

interface DataFeedContextType {
    marketData: Record<string, MarketData>;
    candles: Record<string, CandleData[]>;
    isConnected: boolean;
    subscribe: (symbol: string) => void;
    unsubscribe: (symbol: string) => void;
}

const DataFeedContext = createContext<DataFeedContextType | undefined>(undefined);

export const DataFeedProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
    const [candles, setCandles] = useState<Record<string, CandleData[]>>({});
    const [isConnected, setIsConnected] = useState(false);
    const socketRef = useRef<Socket | null>(null);
    const subscriptions = useRef<Set<string>>(new Set());

    useEffect(() => {
        const socket = io(WS_BASE_URL, {
            path: '/socket.io',
            transports: ['websocket', 'polling'],
            reconnection: true,
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[DataFeed] Connected to real-time feed');
            setIsConnected(true);
            // Re-subscribe to all active symbols
            subscriptions.current.forEach(symbol => {
                socket.emit('subscribe', { symbol });
            });
        });

        socket.on('disconnect', () => {
            console.log('[DataFeed] Disconnected');
            setIsConnected(false);
        });

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
                timestamp: new Date(data.timestamp),
                source: data.source || 'broker'
            };

            setMarketData(prev => ({ ...prev, [symbol]: mData }));

            // Update candles
            setCandles(prev => {
                const symbolCandles = prev[symbol] || [];
                const lastCandle = symbolCandles[symbolCandles.length - 1];
                const newCandle: CandleData = {
                    time: mData.timestamp.toLocaleTimeString(),
                    date: mData.timestamp.toLocaleDateString(),
                    open: data.open,
                    high: data.high,
                    low: data.low,
                    close: data.price,
                    volume: data.volume,
                    symbol
                };

                // If it's a new minute/period, append. Otherwise update last.
                // For simplicity, we'll keep a rolling buffer of 100 candles.
                if (!lastCandle || lastCandle.time !== newCandle.time) {
                    const updated = [...symbolCandles, newCandle].slice(-100);
                    return { ...prev, [symbol]: updated };
                } else {
                    const updated = [...symbolCandles];
                    updated[updated.length - 1] = newCandle;
                    return { ...prev, [symbol]: updated };
                }
            });
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    const subscribe = useCallback((symbol: string) => {
        if (!subscriptions.current.has(symbol)) {
            subscriptions.current.add(symbol);
            if (socketRef.current?.connected) {
                socketRef.current.emit('subscribe', { symbol });
            }
        }
    }, []);

    const unsubscribe = useCallback((symbol: string) => {
        subscriptions.current.delete(symbol);
        // Note: server-side unsubscribe not strictly needed for this demo but good practice
    }, []);

    return (
        <DataFeedContext.Provider value={{ marketData, candles, isConnected, subscribe, unsubscribe }}>
            {children}
        </DataFeedContext.Provider>
    );
};

export const useDataFeed = () => {
    const context = useContext(DataFeedContext);
    if (context === undefined) {
        throw new Error('useDataFeed must be used within a DataFeedProvider');
    }
    return context;
};
