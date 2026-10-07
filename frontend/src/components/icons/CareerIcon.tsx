/**
 * CareerIcon — semantic icon registry for E-Career.
 *
 * Context: audited against LeulAria/Aria-Icons (MIT), which is a CLI/MCP
 * tool for *discovering* icons during development, not a runtime npm
 * dependency. This component borrows that project's underlying philosophy
 * ("pick one icon, write it as source, don't pull in a giant runtime
 * dependency") without installing the `aria-icons` package itself — the
 * frontend already has exactly one icon library (`lucide-react`), used
 * directly at 30+ call sites with zero shared abstraction. This wrapper
 * gives call sites a stable, domain-level vocabulary (`<CareerIcon name="job" />`)
 * instead of importing raw lucide glyphs everywhere, while still rendering
 * plain lucide-react components under the hood (no new dependency, no new
 * design system).
 *
 * Usage:
 *   <CareerIcon name="job" className="h-4 w-4" />
 *   <CareerIcon name="bookmark" active={isSaved} className="h-4 w-4" />      // stateful
 *   <CareerIcon name="refresh" spinning={isLoading} className="h-4 w-4" />  // motion-aware
 *   <CareerIcon name="notification" label="Notifications (3 unread)" />      // standalone a11y
 *
 * Decorative usage (icon next to visible text) should NOT pass `label` —
 * it is rendered `aria-hidden` by default so screen readers don't double
 * announce the adjacent text. Pass `label` only when the icon is the sole
 * content of an interactive element (e.g. inside an icon-only button use
 * `aria-label` on the <Button>, not `label` here).
 */
import {
  type LucideIcon,
  // Core domain
  Briefcase,
  Building2,
  User,
  Users,
  Search,
  Send,
  Bookmark,
  BookmarkCheck,
  FileText,
  GraduationCap,
  ClipboardCheck,
  Mic,
  Sparkles,
  Bell,
  BellRing,
  CreditCard,
  BarChart3,
  Settings,
  ShieldCheck,
  BadgeCheck,
  Landmark,
  LayoutDashboard,
  Target,
  Award,
  MapPin,
  DollarSign,
  Globe,
  Building,
  CalendarDays,
  Mail,
  Phone,
  Upload,
  Download,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  MoreHorizontal,
  Pencil,
  Trash2,
  Copy,
  Share2,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

/**
 * Semantic name -> lucide icon map. Add new entries here rather than
 * importing lucide icons ad hoc at call sites, so the icon vocabulary for
 * the platform stays discoverable in one place.
 */
const ICON_REGISTRY: Record<string, LucideIcon> = {
  // Jobs / hiring
  job: Briefcase,
  company: Building2,
  employer: Building,
  candidate: User,
  talentPool: Users,
  search: Search,
  apply: Send,
  bookmark: Bookmark,
  bookmarkFilled: BookmarkCheck,

  // Career / growth
  cv: FileText,
  career: GraduationCap,
  assessment: ClipboardCheck,
  interview: Mic,
  voice: Mic,
  skills: Target,
  education: GraduationCap,
  experience: Award,

  // AI / platform
  ai: Sparkles,
  rasheed: Sparkles,

  // Notifications / account
  notification: Bell,
  notificationUnread: BellRing,
  billing: CreditCard,
  analytics: BarChart3,
  settings: Settings,
  security: ShieldCheck,
  verification: BadgeCheck,
  government: Landmark,
  admin: LayoutDashboard,

  // Attributes
  location: MapPin,
  salary: DollarSign,
  remote: Globe,

  // Contact / dates
  calendar: CalendarDays,
  email: Mail,
  phone: Phone,

  // File ops
  upload: Upload,
  download: Download,

  // Status
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle,

  // UI chrome
  refresh: RefreshCw,
  back: ArrowLeft,
  forward: ArrowRight,
  more: MoreHorizontal,
  edit: Pencil,
  delete: Trash2,
  copy: Copy,
  share: Share2,
  close: X,
  expand: ChevronDown,
  collapse: ChevronUp,
};

export type CareerIconName = keyof typeof ICON_REGISTRY;

export interface CareerIconProps {
  /** Semantic icon name from the registry. Unknown names fall back to a neutral placeholder. */
  name: CareerIconName | string;
  className?: string;
  /**
   * Toggles a "filled/active" variant where one exists (currently: bookmark).
   * No-op for names without a filled variant.
   */
  active?: boolean;
  /** Applies a continuous spin animation (e.g. refresh-in-progress). Respects prefers-reduced-motion via CSS. */
  spinning?: boolean;
  /**
   * Accessible name for standalone/informational icon usage (e.g. a status
   * icon with no adjacent text). Do not use for icon-only buttons — put
   * aria-label on the button/trigger element instead.
   */
  label?: string;
}

const FALLBACK_ICON: LucideIcon = AlertTriangle;

/**
 * Resolves `name` + `active` to a concrete lucide icon, honoring the one
 * stateful pair we have today (bookmark/bookmarkFilled).
 */
function resolveIcon(name: string, active?: boolean): LucideIcon {
  if (name === "bookmark" && active) return ICON_REGISTRY.bookmarkFilled;
  if (name === "notification" && active) return ICON_REGISTRY.notificationUnread;
  return ICON_REGISTRY[name] ?? FALLBACK_ICON;
}

export function CareerIcon({ name, className, active, spinning, label }: CareerIconProps) {
  const Icon = resolveIcon(name, active);

  return (
    <Icon
      className={spinning ? `${className ?? ""} animate-spin motion-reduce:animate-none` : className}
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
    />
  );
}

/** Returns true if `name` has a registered mapping (useful for conditional rendering/tests). */
export function isKnownCareerIcon(name: string): name is CareerIconName {
  return name in ICON_REGISTRY;
}
