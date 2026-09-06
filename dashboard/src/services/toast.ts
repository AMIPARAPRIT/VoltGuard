import { useState, useEffect } from 'react';

export interface ToastMessage {
  id: string;
  title: string;
  message?: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

class ToastManager {
  private listeners: ((toasts: ToastMessage[]) => void)[] = [];
  private toasts: ToastMessage[] = [];

  subscribe(listener: (toasts: ToastMessage[]) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private emit() {
    this.listeners.forEach((listener) => listener(this.toasts));
  }

  show(toast: Omit<ToastMessage, 'id'>, duration = 3000) {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...toast, id };
    this.toasts = [...this.toasts, newToast];
    this.emit();

    if (duration > 0) {
      setTimeout(() => {
        this.remove(id);
      }, duration);
    }
  }

  remove(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.emit();
  }

  success(title: string, message?: string) {
    this.show({ title, message, type: 'success' });
  }

  error(title: string, message?: string) {
    this.show({ title, message, type: 'error' });
  }

  info(title: string, message?: string) {
    this.show({ title, message, type: 'info' });
  }
}

export const toast = new ToastManager();

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    return toast.subscribe(setToasts);
  }, []);

  return toasts;
}
