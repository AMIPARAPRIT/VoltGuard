import { WebSocketMessage } from '../types';

type MessageHandler = (msg: WebSocketMessage) => void;
type StatusHandler = (status: 'LIVE' | 'DISCONNECTED' | 'CONNECTING') => void;

class WebSocketClientService {
  private ws: WebSocket | null = null;
  private messageListeners: Set<MessageHandler> = new Set();
  private statusListeners: Set<StatusHandler> = new Set();
  private reconnectTimer: number | null = null;
  private currentStatus: 'LIVE' | 'DISCONNECTED' | 'CONNECTING' = 'DISCONNECTED';

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setStatus('CONNECTING');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.setStatus('LIVE');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.notifyMessage(data);
        } catch (e) {
          // Ignore malformed message
        }
      };

      this.ws.onclose = () => {
        this.setStatus('DISCONNECTED');
        this.ws = null;
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.setStatus('DISCONNECTED');
      };
    } catch (e) {
      this.setStatus('DISCONNECTED');
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('DISCONNECTED');
  }

  public subscribeMessage(handler: MessageHandler): () => void {
    this.messageListeners.add(handler);
    return () => this.messageListeners.delete(handler);
  }

  public subscribeStatus(handler: StatusHandler): () => void {
    this.statusListeners.add(handler);
    handler(this.currentStatus);
    return () => this.statusListeners.delete(handler);
  }

  public getStatus(): 'LIVE' | 'DISCONNECTED' | 'CONNECTING' {
    return this.currentStatus;
  }

  private setStatus(status: 'LIVE' | 'DISCONNECTED' | 'CONNECTING'): void {
    if (this.currentStatus !== status) {
      this.currentStatus = status;
      this.statusListeners.forEach((fn) => fn(status));
    }
  }

  private notifyMessage(msg: WebSocketMessage): void {
    this.messageListeners.forEach((fn) => fn(msg));
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimer) {
      this.reconnectTimer = window.setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }
}

export const wsService = new WebSocketClientService();
