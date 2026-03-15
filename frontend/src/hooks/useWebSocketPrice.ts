import { useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'http://localhost:5000';

interface PriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  high24h: number;
  low24h: number;
  volume: number;
  open: number;
  high: number;
  low: number;
  timestamp: Date;
}

interface WebSocketPriceConfig {
  symbol?: string;
  enabled?: boolean;
  updateInterval?: number;
  useRealWebSocket?: boolean;
}

export const useWebSocketPrice = (config: WebSocketPriceConfig = {}) => {
  const {
    symbol = 'BTCUSDT',
    enabled = true,
    updateInterval = 1000,
    useRealWebSocket = true
  } = config;

  const [priceData, setPriceData] = useState<PriceData>({
    symbol,
    price: 47509,
    change: 984,
    changePercent: 2.11,
    high24h: 48500,
    low24h: 46000,
    volume: 1250000000,
    open: 46525,
    high: 48500,
    low: 46000,
    timestamp: new Date(),
  });

  const [isConnected, setIsConnected] = useState(false);
  const [isLive, setIsLive] = useState(enabled);
  const socketRef = useRef<Socket | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const basePrice = useRef(47509);

  // Real WebSocket connection
  useEffect(() => {
    if (!useRealWebSocket || !enabled || !isLive) {
      return;
    }

    // Connect to backend WebSocket
    const socket = io(WS_BASE_URL, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[WebSocket] Connected to backend:', WS_BASE_URL);
      setIsConnected(true);

      // Subscribe to symbol
      socket.emit('subscribe', { symbol });
    });

    socket.on('disconnect', () => {
      console.log('[WebSocket] Disconnected from backend');
      setIsConnected(false);
    });

    socket.on('price_update', (data: any) => {
      if (data.symbol === symbol || data.symbol?.includes(symbol.replace('USDT', ''))) {
        setPriceData(prev => ({
          ...prev,
          symbol: data.symbol || symbol,
          price: data.price || data.close || prev.price,
          open: data.open || prev.open,
          high: data.high || prev.high,
          low: data.low || prev.low,
          volume: data.volume || prev.volume,
          change: data.change || prev.change,
          changePercent: data.changePercent || prev.changePercent,
          high24h: Math.max(prev.high24h, data.high || prev.high),
          low24h: Math.min(prev.low24h, data.low || prev.low),
          timestamp: new Date(data.timestamp || Date.now()),
        }));
      }
    });

    socket.on('subscribed', (data: any) => {
      console.log('[WebSocket] Subscribed to:', data.symbol);
    });

    socket.on('connected', (data: any) => {
      console.log('[WebSocket] Connected event:', data);
    });

    socket.on('error', (error: any) => {
      console.error('[WebSocket] Error:', error);
    });

    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [useRealWebSocket, enabled, isLive, symbol]);

  // Fallback simulation when WebSocket is not available
  const generatePriceUpdate = useCallback(() => {
    const volatility = 0.001;
    const drift = (Math.random() - 0.5) * 2;
    const change = basePrice.current * volatility * drift;

    basePrice.current += change;

    const newPrice = basePrice.current;
    const dailyChange = newPrice - 46525;
    const dailyChangePercent = (dailyChange / 46525) * 100;

    setPriceData(prev => ({
      ...prev,
      symbol,
      price: Number(newPrice.toFixed(2)),
      change: Number(dailyChange.toFixed(2)),
      changePercent: Number(dailyChangePercent.toFixed(2)),
      high24h: Math.max(prev.high24h, newPrice),
      low24h: Math.min(prev.low24h, newPrice),
      volume: prev.volume + Math.random() * 1000000,
      timestamp: new Date(),
    }));
  }, [symbol]);

  // Fallback to simulation if WebSocket not connected
  useEffect(() => {
    if (!useRealWebSocket && isLive && enabled) {
      setIsConnected(true);
      intervalRef.current = setInterval(generatePriceUpdate, updateInterval);
      console.log('[Simulation] Started simulated price feed:', symbol);
    } else if (!isConnected && isLive && enabled) {
      // Fallback simulation when real WebSocket fails
      const fallbackTimer = setTimeout(() => {
        if (!isConnected) {
          console.log('[Simulation] Falling back to simulated data');
          intervalRef.current = setInterval(generatePriceUpdate, updateInterval);
        }
      }, 5000);

      return () => clearTimeout(fallbackTimer);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [useRealWebSocket, isLive, enabled, isConnected, updateInterval, generatePriceUpdate, symbol]);

  const toggleConnection = useCallback(() => {
    setIsLive(prev => !prev);
    if (isLive && socketRef.current) {
      socketRef.current.disconnect();
    }
  }, [isLive]);

  const setSymbol = useCallback((newSymbol: string) => {
    setPriceData(prev => ({ ...prev, symbol: newSymbol }));
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit('subscribe', { symbol: newSymbol });
    }
  }, []);

  const reconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.connect();
    }
  }, []);

  return {
    priceData,
    isConnected,
    isLive,
    toggleConnection,
    setSymbol,
    reconnect,
  };
};

export default useWebSocketPrice;
