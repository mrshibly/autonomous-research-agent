import { useState, useEffect, useCallback, useRef } from 'react';
import { getResearchStatus } from '../services/api';

/**
 * Custom hook to follow research task status in real-time.
 * Uses WebSockets for live updates and falls back to HTTP polling.
 */
export function useResearchStatus(taskId) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    if (!taskId) return;
    try {
      setLoading(true);
      const data = await getResearchStatus(taskId);
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (!taskId) return;

    // Initial fetch
    fetchStatus();

    // Connect WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${taskId}`;
    
    const connectWS = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'status_update') {
          setStatus((prev) => ({ ...prev, ...message.data }));
        }
      };

      ws.onclose = () => {
        // Fallback to polling if WebSocket disconnects
        const interval = setInterval(() => {
          if (status?.status === 'completed' || status?.status === 'failed') {
            clearInterval(interval);
            return;
          }
          fetchStatus();
        }, 3000);
        return () => clearInterval(interval);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws.close();
      };
    };

    connectWS();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [taskId, fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
}
