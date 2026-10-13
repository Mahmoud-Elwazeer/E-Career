import { useEffect, useState } from "react";
import { Cookie, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useTheme } from "@/hooks/use-theme";
import {
  listCookieCategories, getMyCookieConsent, recordCookieConsent,
  type CookieCategoryDef, type CookieAction,
} from "@/services/legal";

type Prefs = Record<string, boolean>;

const LOCAL_SEEN_KEY = "usam_cookie_consent_seen";

/**
 * Global cookie-consent banner + preference manager.
 *
 * Directive-mandated behavior:
 *  - Offers Accept All / Reject Non-Essential / Manage Preferences — never
 *    just a single "Accept" button (no dark patterns).
 *  - Works for anonymous visitors (backend ties the record to a session key)
 *    and NEVER blocks login — necessary cookies are always on and the
 *    banner itself never gates any auth action.
 *  - Every choice is recorded server-side (versioned to the active Cookie
 *    Policy) via POST /legal/cookie-consent/, not just local storage, so
 *    it's auditable. A local flag only controls whether we show the banner
 *    again on this device.
 */
export function CookieConsentBanner() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  const [categories, setCategories] = useState<CookieCategoryDef[]>([]);
  const [visible, setVisible] = useState(false);
  const [manageOpen, setManageOpen] = useState(false);
  const [prefs, setPrefs] = useState<Prefs>({ necessary: true, functional: false, analytics: false, marketing: false });
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [cats, existing] = await Promise.all([
          listCookieCategories(),
          getMyCookieConsent(),
        ]);
        if (!active) return;
        setCategories(cats);
        if (existing) {
          setPrefs({ necessary: true, ...existing.categories });
          setVisible(false);
        } else if (!localStorage.getItem(LOCAL_SEEN_KEY)) {
          setVisible(true);
        }
      } catch {
        // Fail silently/open — the banner must never block the rest of the
        // app from loading if the API is briefly unavailable.
      } finally {
        if (active) setLoaded(true);
      }
    })();
    return () => { active = false; };
  }, []);

  // Lets a "Cookie settings" link anywhere in the app (e.g. footer) reopen
  // the preference manager without re-showing the full bottom banner.
  useEffect(() => {
    const handler = () => setManageOpen(true);
    window.addEventListener("usam:open-cookie-preferences", handler);
    return () => window.removeEventListener("usam:open-cookie-preferences", handler);
  }, []);

  const persist = async (action: CookieAction, categoriesToSave: Prefs) => {
    setSaving(true);
    try {
      await recordCookieConsent(action, { ...categoriesToSave, necessary: true });
      localStorage.setItem(LOCAL_SEEN_KEY, "true");
      setVisible(false);
      setManageOpen(false);
    } catch {
      // If the API call fails, still dismiss locally rather than trap the
      // user behind a banner they can't get rid of — necessary cookies work
      // regardless, and they can reopen "Manage preferences" from the footer.
      localStorage.setItem(LOCAL_SEEN_KEY, "true");
      setVisible(false);
      setManageOpen(false);
    } finally {
      setSaving(false);
    }
  };

  const acceptAll = () => persist("accept_all", { necessary: true, functional: true, analytics: true, marketing: true });
  const rejectNonEssential = () => persist("reject_non_essential", { necessary: true, functional: false, analytics: false, marketing: false });
  const saveCustom = () => persist("custom", prefs);

  if (!loaded) return null;

  return (
    <>
      {visible && (
        <div
          role="region"
          aria-label={isAr ? "إشعار ملفات تعريف الارتباط" : "Cookie notice"}
          className="fixed inset-x-0 bottom-0 z-[100] border-t border-border bg-card/98 backdrop-blur-sm shadow-2xl"
        >
          <div className="container flex flex-col gap-4 py-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3 md:max-w-xl">
              <Cookie className="h-5 w-5 shrink-0 text-primary mt-0.5" />
              <p className="text-body text-muted-foreground">
                {isAr
                  ? "نستخدم ملفات تعريف الارتباط الضرورية لتشغيل المنصة. يمكنك قبول الكل أو رفض غير الضروري أو إدارة التفضيلات."
                  : "We use cookies to run the platform. Necessary cookies are always on. You can accept all, reject non-essential, or manage your preferences."}
                {" "}
                <a href="/legal/cookies" className="text-primary link-underline">
                  {isAr ? "سياسة ملفات تعريف الارتباط" : "Cookie Policy"}
                </a>
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" onClick={() => setManageOpen(true)} disabled={saving} className="gap-1.5">
                <Settings2 className="h-3.5 w-3.5" /> {isAr ? "إدارة التفضيلات" : "Manage preferences"}
              </Button>
              <Button variant="outline" size="sm" onClick={rejectNonEssential} disabled={saving}>
                {isAr ? "رفض غير الضروري" : "Reject non-essential"}
              </Button>
              <Button size="sm" onClick={acceptAll} disabled={saving}>
                {isAr ? "قبول الكل" : "Accept all"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <Dialog open={manageOpen} onOpenChange={setManageOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{isAr ? "تفضيلات ملفات تعريف الارتباط" : "Cookie preferences"}</DialogTitle>
            <DialogDescription>
              {isAr
                ? "ملفات تعريف الارتباط الضرورية مفعّلة دائماً ولا يمكن إيقافها. اختر الفئات الأخرى بحرية."
                : "Necessary cookies are always on and can't be turned off. Choose the rest freely."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {(categories.length ? categories : [
              { key: "necessary", label: "Strictly necessary", description: "", is_essential: true, is_active: true, uuid: "necessary" },
              { key: "functional", label: "Functional", description: "", is_essential: false, is_active: true, uuid: "functional" },
              { key: "analytics", label: "Analytics", description: "", is_essential: false, is_active: true, uuid: "analytics" },
              { key: "marketing", label: "Marketing", description: "", is_essential: false, is_active: true, uuid: "marketing" },
            ] as CookieCategoryDef[]).map((cat) => (
              <div key={cat.key} className="flex items-start justify-between gap-4 rounded-xl border border-border p-3">
                <div>
                  <Label className="font-medium">{cat.label}</Label>
                  {cat.description && <p className="text-caption text-muted-foreground mt-0.5">{cat.description}</p>}
                </div>
                <Switch
                  checked={cat.is_essential ? true : !!prefs[cat.key]}
                  disabled={cat.is_essential}
                  onCheckedChange={(v) => setPrefs((p) => ({ ...p, [cat.key]: v }))}
                  aria-label={cat.label}
                />
              </div>
            ))}
          </div>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={rejectNonEssential} disabled={saving}>
              {isAr ? "رفض غير الضروري" : "Reject non-essential"}
            </Button>
            <Button onClick={saveCustom} disabled={saving}>
              {isAr ? "حفظ التفضيلات" : "Save preferences"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/** Imperatively reopen the manager — used by a "Cookie settings" footer link. */
export function openCookiePreferences() {
  window.dispatchEvent(new CustomEvent("usam:open-cookie-preferences"));
}
