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
  const statusRef = useRef(null);
  const intervalRef = useRef(null);

  // Keep statusRef in sync
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const fetchStatus = useCallback(async () => {
    if (!taskId) return;
    try {
      setLoading(true);
      const data = await getResearchStatus(taskId);
      setStatus(data);
      setError(null);

      // Stop polling if terminal state
      if (data?.status === 'completed' || data?.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      // Stop polling on 404 (task deleted / doesn't exist after restart)
      if (err.message?.includes('404') || err.message?.includes('not found') || err.message?.includes('Not Found')) {
        setError('Research task not found. It may have been removed after a system restart.');
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        setError(err.message);
      }
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
        // Only start polling if not already in a terminal state
        const current = statusRef.current;
        if (current?.status === 'completed' || current?.status === 'failed') {
          return;
        }

        // Fallback to polling if WebSocket disconnects
        intervalRef.current = setInterval(() => {
          const s = statusRef.current;
          if (s?.status === 'completed' || s?.status === 'failed') {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
            return;
          }
          fetchStatus();
        }, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws.close();
      };
    };

    connectWS();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskId, fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
}
