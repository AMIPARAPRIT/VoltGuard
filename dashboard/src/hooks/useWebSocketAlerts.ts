/**
 * useWebSocketAlerts — React hook that subscribes to the global WebSocket
 * service and fires callbacks whenever a new alert-related message arrives.
 *
 * Encapsulates:
 * - Subscription lifecycle management (mount / unmount cleanup)
 * - Filtering to only forward `security_event` messages that carry an alert_id
 * - Returns live WS connection status for UI indicators
 */

import { useEffect, useCallback, useState } from 'react';
import { wsService } from '../services/websocket';
import { WebSocketMessage } from '../types';

export type WsStatus = 'LIVE' | 'DISCONNECTED' | 'CONNECTING';

interface UseWebSocketAlertsOptions {
  /** Called when a WS message with alert_id arrives (new alert generated). */
  onNewAlert?: (msg: WebSocketMessage) => void;
  /** Called for every WS message, regardless of type. */
  onMessage?: (msg: WebSocketMessage) => void;
}

export function useWebSocketAlerts(options: UseWebSocketAlertsOptions = {}) {
  const { onNewAlert, onMessage } = options;
  const [wsStatus, setWsStatus] = useState<WsStatus>(wsService.getStatus());

  const handleMessage = useCallback(
    (msg: WebSocketMessage) => {
      if (onMessage) {
        onMessage(msg);
      }
      if (onNewAlert && msg.type === 'security_event' && msg.alert_id != null) {
        onNewAlert(msg);
      }
    },
    [onMessage, onNewAlert]
  );

  useEffect(() => {
    // Subscribe to WS messages
    const unsubMessage = wsService.subscribeMessage(handleMessage);
    // Subscribe to connection status
    const unsubStatus = wsService.subscribeStatus(setWsStatus);

    return () => {
      unsubMessage();
      unsubStatus();
    };
  }, [handleMessage]);

  return { wsStatus };
}
