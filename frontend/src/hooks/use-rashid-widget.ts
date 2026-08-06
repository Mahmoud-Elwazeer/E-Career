/**
 * useRashidWidget Hook
 * Controls the Rashid floating widget
 */

import { useCallback } from 'react';

export function useRashidWidget() {
  const openWidget = useCallback(() => {
    // Trigger the widget to open
    const event = new CustomEvent('rashid:open');
    window.dispatchEvent(event);
  }, []);

  return {
    openWidget,
  };
}
