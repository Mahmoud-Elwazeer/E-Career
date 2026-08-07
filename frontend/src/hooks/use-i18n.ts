import { useEffect } from 'react';
import { useTheme } from './use-theme';
import i18n from '@/i18n/i18n';

/**
 * Hook to sync i18n language with the theme language
 * This ensures that when the user changes language via the theme toggle,
 * i18n also updates to the correct language
 */
export function useI18nSync() {
  const { lang } = useTheme();

  useEffect(() => {
    // Only update i18n if the language has changed
    if (i18n.language !== lang) {
      i18n.changeLanguage(lang);
    }
  }, [lang]);

  return { t: i18n.t, i18n };
}