/**
 * WebSocket Hook for Real-time Updates
 */

import { useEffect, useRef, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/ui';

export const useWebSocket = (onMessage) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep the ref updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          console.log('✅ WebSocket connected');
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);
            setLastMessage(data);

            if (onMessageRef.current) {
              onMessageRef.current(data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          setIsConnected(false);

          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            connect();
          }, 3000);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('Error creating WebSocket:', error);
      }
    };

    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []); // Remove onMessage dependency to prevent reconnection loop

  // Send message function
  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  // Send ping to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(() => {
        sendMessage({ type: 'ping' });
      }, 30000); // Every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [isConnected]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
};
