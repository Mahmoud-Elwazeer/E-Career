import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Send, X, Sparkles, ArrowRight, Loader2 } from "lucide-react";
import { RasheedAvatar, type RasheedExpression } from "./RasheedAvatar";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";
import { apiRequest } from "@/services/client";

/**
 * RasheedCompanion — a persistent, interactive assistant present on EVERY page
 * (public + authenticated).
 *
 * - Floating professional avatar (RasheedAvatar) bottom-end.
 * - Proactive, route-aware speech bubbles that surface periodically.
 * - Ask/answer mini-chat:
 *     • authenticated → real LLM via /intelligence/rashid/chat/
 *     • anonymous     → curated platform Q&A (quick answers) + sign-in CTA
 * - Bilingual (EN/AR), RTL-aware, reduced-motion safe.
 */

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
}

/** Tool identifiers dispatched by AskRashidButton / AskRashidCard. */
type RashidTool =
  | "analyze_job"
  | "cover_letter"
  | "interview_prep"
  | "cv_review"
  | "linkedin_optimizer"
  | "course_advisor"
  | "career_path";

/**
 * Build a natural-language prompt for a tool request so the existing LLM chat
 * endpoint handles it — no new backend contract needed. Job context (slug) is
 * folded into the message when present.
 */
function toolPrompt(tool: RashidTool, context: Record<string, unknown>, isAr: boolean): string {
  const slug = typeof context?.jobSlug === "string" ? context.jobSlug : undefined;
  const jobRef = slug ? (isAr ? ` (الوظيفة: ${slug})` : ` (job: ${slug})`) : "";
  const en: Record<RashidTool, string> = {
    analyze_job: `Analyze this job and how well it fits my profile${jobRef}.`,
    cover_letter: `Help me write a cover letter for this job${jobRef}.`,
    interview_prep: `Prepare me for an interview for this job${jobRef}.`,
    cv_review: `Review my CV and suggest improvements${jobRef}.`,
    linkedin_optimizer: `Help me optimize my LinkedIn profile.`,
    course_advisor: `Recommend courses to close my skill gaps${jobRef}.`,
    career_path: `Map out a career path for me${jobRef}.`,
  };
  const ar: Record<RashidTool, string> = {
    analyze_job: `حلّل هذه الوظيفة ومدى ملاءمتها لملفي${jobRef}.`,
    cover_letter: `ساعدني في كتابة خطاب تغطية لهذه الوظيفة${jobRef}.`,
    interview_prep: `جهّزني لمقابلة هذه الوظيفة${jobRef}.`,
    cv_review: `راجع سيرتي الذاتية واقترح تحسينات${jobRef}.`,
    linkedin_optimizer: `ساعدني في تحسين ملفي على لينكدإن.`,
    course_advisor: `اقترح دورات لسدّ فجوات مهاراتي${jobRef}.`,
    career_path: `ارسم لي مساراً مهنياً${jobRef}.`,
  };
  return (isAr ? ar : en)[tool] ?? (isAr ? "ساعدني." : "Help me.");
}

/* Proactive nudges shown periodically, keyed by route intent. */
function useProactiveMessages(pathname: string, isAr: boolean, _isAuthed: boolean) {
  return useCallback((): string[] => {
    if (pathname === "/" || pathname === "") {
      return isAr
        ? ["أهلاً! أنا رشيد 👋 اسألني عن أي شيء في المنصة.", "هل تبحث عن وظيفة معينة؟ أقدر أساعدك."]
        : ["Hi! I'm Rasheed 👋 Ask me anything about the platform.", "Looking for a specific role? I can help you find it."];
    }
    if (pathname.startsWith("/pricing")) {
      return isAr ? ["تحتار في اختيار الباقة؟ اسألني."] : ["Not sure which plan fits? Ask me."];
    }
    if (pathname.startsWith("/app/jobs")) {
      return isAr ? ["أقدر ألخّص أي وظيفة أو أقارنها بملفك."] : ["I can summarize any job or compare it to your profile."];
    }
    if (pathname.startsWith("/app/resume")) {
      return isAr ? ["تريد مراجعة سيرتك الذاتية؟"] : ["Want me to review your CV?"];
    }
    if (pathname.startsWith("/for-individuals")) {
      return isAr ? ["أخبرني عن مجالك وسأقترح لك الخطوة التالية."] : ["Tell me your field and I'll suggest your next step."];
    }
    if (pathname.startsWith("/for-businesses")) {
      return isAr ? ["توظّف؟ أقدر أشرح كيف نرتّب المرشحين لك."] : ["Hiring? I can explain how we rank candidates for you."];
    }
    if (pathname.startsWith("/app/employer")) {
      return isAr ? ["أقدر أساعدك تكتب وصف وظيفة أو تفرز المتقدمين."] : ["I can help you write a job post or screen applicants."];
    }
    if (pathname.startsWith("/app/dashboard")) {
      return isAr ? ["أهلاً بعودتك 👋 تريد أن نكمل من حيث توقفت؟"] : ["Welcome back 👋 Want to pick up where you left off?"];
    }
    if (pathname.startsWith("/contact") || pathname.startsWith("/about")) {
      return isAr ? ["عندك سؤال عن المنصة؟ اسألني هنا مباشرة."] : ["Question about the platform? Ask me right here."];
    }
    return isAr ? ["أنا هنا إذا احتجت مساعدة 🙂"] : ["I'm here if you need a hand 🙂"];
    // isAuthed intentionally omitted: messages are keyed by route + language.
  }, [pathname, isAr]);
}

/* Curated public answers for anonymous visitors (no auth-gated LLM). */
function publicAnswer(q: string, isAr: boolean): string {
  const t = q.toLowerCase();
  const has = (...k: string[]) => k.some((w) => t.includes(w));
  if (has("apply", "قدّم", "تقديم"))
    return isAr
      ? "نوجّهك مباشرة إلى المصدر الأصلي لصاحب العمل — بدون وسطاء. سجّل الدخول للتقديم وحفظ الوظائف."
      : "We link you straight to the employer's original source — no middlemen. Sign in to apply and save jobs.";
  if (has("price", "cost", "plan", "سعر", "باقة", "تكلفة"))
    return isAr
      ? "التصفح والبحث مجاني للأفراد. لأصحاب العمل هناك باقات — تفضل صفحة الأسعار."
      : "Browsing and searching are free for individuals. Employers have plans — see the Pricing page.";
  if (has("employer", "hire", "post a job", "صاحب عمل", "توظيف", "نشر"))
    return isAr
      ? "أصحاب العمل ينشرون الوظائف ويبحثون في قاعدة المواهب. أنشئ حساب شركة للبدء."
      : "Employers can post jobs and search the talent pool. Create a company account to get started.";
  if (has("cv", "resume", "سيرة"))
    return isAr
      ? "لدينا منشئ سيرة ذاتية ومراجعة بالذكاء الاصطناعي. سجّل الدخول لتجربتها."
      : "We have a resume builder and AI review. Sign in to try them.";
  if (has("who", "what is", "rasheed", "رشيد", "منصة", "usam"))
    return isAr
      ? "أنا رشيد، مساعدك المهني في USAM — منصة تجمع الوظائف الموثوقة عبر الشرق الأوسط وتساعدك من البحث حتى التوظيف."
      : "I'm Rasheed, your career coach on USAM — a platform that aggregates verified jobs across MENA and guides you from search to hire.";
  return isAr
    ? "سؤال ممتاز! للحصول على إجابة كاملة مدعومة بالذكاء الاصطناعي، سجّل الدخول وسأساعدك بالتفصيل."
    : "Great question! For a full AI-powered answer, sign in and I'll help you in detail.";
}

const SUGGESTIONS_PUBLIC = [
  { en: "What is USAM?", ar: "ما هي USAM؟" },
  { en: "How do I apply?", ar: "كيف أقدّم؟" },
  { en: "Is it free?", ar: "هل هي مجانية؟" },
  { en: "I'm an employer", ar: "أنا صاحب عمل" },
];

export function RasheedCompanion() {
  const { isAuthenticated } = useAuth();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const location = useLocation();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [bubble, setBubble] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [expr, setExpr] = useState<RasheedExpression>("idle");
  const endRef = useRef<HTMLDivElement>(null);
  const bubbleTimer = useRef<ReturnType<typeof setTimeout>>();

  const getMessages = useProactiveMessages(location.pathname, isAr, isAuthenticated);

  // Proactive bubbles: first after 3.5s, then rotate every ~30s while closed.
  useEffect(() => {
    if (open) { setBubble(null); return; }
    const msgs = getMessages();
    let i = 0;
    const show = () => {
      setBubble(msgs[i % msgs.length]);
      setExpr("greeting");
      i++;
      bubbleTimer.current = setTimeout(() => {
        setBubble(null);
        setExpr("idle");
        bubbleTimer.current = setTimeout(show, 26000);
      }, 6000);
    };
    const first = setTimeout(show, 3500);
    return () => { clearTimeout(first); if (bubbleTimer.current) clearTimeout(bubbleTimer.current); };
  }, [open, location.pathname, getMessages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const greet = useCallback(() => {
    if (messages.length === 0) {
      setMessages([{ role: "assistant", content: isAr ? "أهلاً! أنا رشيد. كيف أقدر أساعدك اليوم؟" : "Hi! I'm Rasheed. How can I help you today?" }]);
    }
  }, [messages.length, isAr]);

  const send = useCallback(async (text: string) => {
    const q = text.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setBusy(true);
    setExpr("thinking");

    try {
      if (isAuthenticated) {
        const data = await apiRequest<{ response?: string; message?: string }>(
          "/intelligence/rashid/chat/",
          { method: "POST", body: { message: q, language: isAr ? "ar" : "en" } }
        );
        const reply = data.response || data.message || (isAr ? "عذراً، حصل خطأ بسيط. حاول مرة أخرى." : "Sorry, something went wrong. Please try again.");
        setExpr("talking");
        setMessages((m) => [...m, { role: "assistant", content: reply }]);
      } else {
        await new Promise((r) => setTimeout(r, 500));
        setExpr("talking");
        setMessages((m) => [...m, { role: "assistant", content: publicAnswer(q, isAr) }]);
      }
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: isAr ? "تعذّر الاتصال. حاول لاحقاً." : "Couldn't connect. Try again shortly." }]);
    } finally {
      setBusy(false);
      setTimeout(() => setExpr("idle"), 1500);
    }
  }, [busy, isAuthenticated, isAr]);

  const toggle = () => {
    setOpen((o) => {
      if (!o) { setBubble(null); greet(); }
      return !o;
    });
  };

  // Listen for tool/open requests dispatched by AskRashidButton / AskRashidCard
  // elsewhere in the app (e.g. Job Detail). This is what makes "Ask Rasheed
  // about this job" actually do something — previously these events had no
  // listener because the old RashidWidget was never mounted.
  useEffect(() => {
    const openTool = (e: Event) => {
      const detail = (e as CustomEvent).detail ?? {};
      const tool = detail.tool as RashidTool | undefined;
      const context = (detail.context ?? {}) as Record<string, unknown>;
      setBubble(null);
      setOpen(true);
      greet();
      if (tool) {
        // Let the panel mount, then send the tool prompt through the normal path.
        setTimeout(() => send(toolPrompt(tool, context, isAr)), 150);
      }
    };
    const openChat = () => { setBubble(null); setOpen(true); greet(); };

    window.addEventListener("rashid:open-tool", openTool as EventListener);
    window.addEventListener("rashid:open", openChat as EventListener);
    return () => {
      window.removeEventListener("rashid:open-tool", openTool as EventListener);
      window.removeEventListener("rashid:open", openChat as EventListener);
    };
  }, [greet, send, isAr]);

  const side = dir === "rtl" ? "start-4 md:start-6" : "end-4 md:end-6";

  return (
    <div className={`fixed bottom-5 ${side} z-[60] flex flex-col items-end gap-3`}>
      {/* Mini chat panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, y: 24, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 260, damping: 24 }}
            className="w-[92vw] max-w-[380px] h-[540px] max-h-[72vh] overflow-hidden rounded-3xl border border-border bg-card shadow-2xl flex flex-col"
          >
            {/* Header */}
            <div className="hero-gradient relative flex items-center gap-3 p-4 text-primary-foreground">
              <RasheedAvatar expression={expr} size={44} ring={false} />
              <div className="min-w-0">
                <p className="font-semibold leading-tight">{isAr ? "رشيد" : "Rasheed"}</p>
                <p className="text-caption opacity-80 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-secondary" />
                  {isAr ? "مساعدك المهني" : "AI Career Coach"}
                </p>
              </div>
              <button onClick={() => setOpen(false)} aria-label="Close" className="ms-auto rounded-full p-1.5 hover:bg-primary-foreground/15 transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface-2/40">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-body ${
                    m.role === "user"
                      ? "ms-auto bg-primary text-primary-foreground rounded-br-md"
                      : "me-auto bg-card border border-border rounded-bl-md"
                  }`}
                >
                  {m.content}
                </div>
              ))}
              {busy && (
                <div className="me-auto flex items-center gap-2 rounded-2xl border border-border bg-card px-3.5 py-2.5 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isAr ? "يكتب…" : "Typing…"}
                </div>
              )}

              {/* Suggestions */}
              {messages.length <= 1 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {SUGGESTIONS_PUBLIC.map((s) => (
                    <button
                      key={s.en}
                      onClick={() => send(isAr ? s.ar : s.en)}
                      className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-caption font-medium text-primary hover:bg-primary/10 transition-colors"
                    >
                      {isAr ? s.ar : s.en}
                    </button>
                  ))}
                </div>
              )}

              {/* Sign-in upsell for anonymous */}
              {!isAuthenticated && messages.length > 1 && (
                <Link
                  to="/login"
                  className="me-auto inline-flex items-center gap-1.5 rounded-xl bg-secondary px-3.5 py-2 text-caption font-semibold text-[hsl(var(--primary))] shadow-sm"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {isAr ? "سجّل الدخول للمساعد الكامل" : "Sign in for the full AI coach"}
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
              <div ref={endRef} />
            </div>

            {/* Input */}
            <form
              onSubmit={(e) => { e.preventDefault(); send(input); }}
              className="flex items-center gap-2 border-t border-border p-3"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isAr ? "اكتب رسالتك…" : "Ask Rasheed…"}
                className="flex-1 rounded-full bg-muted px-4 py-2.5 text-body focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <button
                type="submit"
                disabled={!input.trim() || busy}
                aria-label="Send"
                className="rounded-full bg-primary p-2.5 text-primary-foreground disabled:opacity-40 press-feedback"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Proactive bubble */}
      <AnimatePresence>
        {bubble && !open && (
          <motion.button
            onClick={toggle}
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="max-w-[240px] rounded-2xl rounded-be-md border border-border bg-card px-4 py-2.5 text-start text-body shadow-xl"
          >
            {bubble}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Floating avatar trigger */}
      <motion.button
        onClick={toggle}
        aria-label={isAr ? "افتح مساعد رشيد" : "Open Rasheed assistant"}
        className="relative rounded-full shadow-xl"
        whileHover={reduced ? undefined : { scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
      >
        <RasheedAvatar expression={open ? "idle" : expr} size={64} />
      </motion.button>
    </div>
  );
}
