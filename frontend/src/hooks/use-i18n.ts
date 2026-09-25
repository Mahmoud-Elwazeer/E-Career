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
    // Defensive: an i18n failure must never crash the whole app shell.
    try {
      if (i18n.language !== lang) {
        i18n.changeLanguage(lang);
      }
      const dir = lang === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.dir = dir;
      document.documentElement.lang = lang;
      document.body.dir = dir;
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn('i18n sync failed (non-fatal):', err);
    }
  }, [lang]);

  return { t: i18n.t, i18n };
}