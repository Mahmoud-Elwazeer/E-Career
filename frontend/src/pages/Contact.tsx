import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Building2, UserRound, LifeBuoy, Send, ArrowRight, ArrowLeft } from "lucide-react";
import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";

/**
 * Contact — a real contact experience. There is no backend contact endpoint
 * yet, so the form composes a pre-filled email via the user's mail client
 * (works today, nothing faked) and we surface the direct support address plus
 * the correct self-serve paths for each audience.
 */
const SUPPORT_EMAIL = "support@usamif.com";

export default function Contact() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

  usePageMeta(
    isAr ? "تواصل معنا" : "Contact us",
    isAr ? "تواصل مع فريق USAM للدعم أو الاستفسارات." : "Get in touch with the USAM team for support or inquiries.",
  );

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [topic, setTopic] = useState(isAr ? "استفسار عام" : "General inquiry");
  const [message, setMessage] = useState("");

  const mailto = () => {
    const subject = encodeURIComponent(`[USAM] ${topic}${name ? ` — ${name}` : ""}`);
    const body = encodeURIComponent(
      `${message}\n\n—\n${name}${email ? ` <${email}>` : ""}`.trim(),
    );
    window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
  };

  const channels = [
    {
      icon: UserRound,
      titleEn: "Job seekers", titleAr: "الباحثون عن عمل",
      descEn: "Questions about your profile, CV, matches or applications.",
      descAr: "أسئلة حول ملفك أو سيرتك أو المطابقات أو الطلبات.",
      to: "/for-individuals", ctaEn: "Explore individuals", ctaAr: "استكشف للأفراد",
    },
    {
      icon: Building2,
      titleEn: "Employers", titleAr: "أصحاب العمل",
      descEn: "Posting roles, sourcing talent, or setting up a company plan.",
      descAr: "نشر الوظائف أو البحث عن المواهب أو إعداد خطة شركة.",
      to: "/for-businesses", ctaEn: "Explore businesses", ctaAr: "استكشف للشركات",
    },
    {
      icon: LifeBuoy,
      titleEn: "Support", titleAr: "الدعم",
      descEn: "Account, billing or technical help from the USAM team.",
      descAr: "مساعدة في الحساب أو الفوترة أو المشكلات التقنية.",
      to: "/pricing", ctaEn: "See plans", ctaAr: "شاهد الباقات",
    },
  ];

  return (
    <Layout>
      <section className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 340, height: 340, top: -120, insetInlineEnd: -80, background: "hsl(var(--secondary) / 0.28)" }} />
        <div className="container relative z-10 max-w-3xl py-16 text-center md:py-20">
          <span className="eyebrow-mono text-primary-foreground/70 mb-4 justify-center">
            <span className="signal-dot" /> {isAr ? "تواصل معنا" : "CONTACT US"}
          </span>
          <h1 className="text-display-serif mt-3 mb-4">{isAr ? "نحن هنا لمساعدتك" : "We're here to help"}</h1>
          <p className="text-body-lg opacity-80">
            {isAr
              ? "اختر المسار المناسب لك أو راسل فريقنا مباشرة — نرد عادةً خلال يوم عمل."
              : "Pick the path that fits you, or message our team directly — we usually reply within one business day."}
          </p>
        </div>
      </section>

      <section className="section-y">
        <div className="container grid gap-10 lg:grid-cols-2">
          {/* Channels */}
          <div className="space-y-4">
            {channels.map((c) => (
              <div key={c.titleEn} className="card-premium flex items-start gap-4 p-6">
                <span className="icon-tile h-12 w-12 shrink-0"><c.icon className="h-6 w-6 text-primary" /></span>
                <div className="min-w-0">
                  <h3 className="text-heading-3 font-semibold mb-1">{isAr ? c.titleAr : c.titleEn}</h3>
                  <p className="text-body text-muted-foreground leading-relaxed">{isAr ? c.descAr : c.descEn}</p>
                  <Link to={c.to} className="mt-3 inline-flex items-center gap-1 text-caption font-medium text-primary link-underline">
                    {isAr ? c.ctaAr : c.ctaEn} <Arrow className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
            <div className="card-premium flex items-center gap-3 p-6">
              <span className="icon-tile h-12 w-12 shrink-0"><Mail className="h-6 w-6 text-primary" /></span>
              <div>
                <p className="text-caption text-muted-foreground">{isAr ? "راسلنا مباشرة" : "Email us directly"}</p>
                <a href={`mailto:${SUPPORT_EMAIL}`} className="text-body font-semibold text-foreground link-underline">
                  {SUPPORT_EMAIL}
                </a>
              </div>
            </div>
          </div>

          {/* Form (composes an email — no backend needed) */}
          <div className="card-premium p-6 md:p-8">
            <h2 className="text-heading-2 mb-1">{isAr ? "أرسل رسالة" : "Send a message"}</h2>
            <p className="text-body text-muted-foreground mb-6">
              {isAr ? "سنفتح تطبيق البريد لديك برسالة جاهزة." : "This opens your email app with a ready-to-send message."}
            </p>
            <form
              onSubmit={(e) => { e.preventDefault(); mailto(); }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="c-name">{isAr ? "الاسم" : "Name"}</Label>
                  <Input id="c-name" value={name} onChange={(e) => setName(e.target.value)} required className="mt-1" />
                </div>
                <div>
                  <Label htmlFor="c-email">{isAr ? "البريد الإلكتروني" : "Email"}</Label>
                  <Input id="c-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="mt-1" />
                </div>
              </div>
              <div>
                <Label htmlFor="c-topic">{isAr ? "الموضوع" : "Topic"}</Label>
                <select
                  id="c-topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-body focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {(isAr
                    ? ["استفسار عام", "دعم فني", "أصحاب العمل والتوظيف", "الفوترة", "شراكات"]
                    : ["General inquiry", "Technical support", "Employers & hiring", "Billing", "Partnerships"]
                  ).map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="c-message">{isAr ? "الرسالة" : "Message"}</Label>
                <Textarea id="c-message" value={message} onChange={(e) => setMessage(e.target.value)} required rows={5} className="mt-1" />
              </div>
              <Button type="submit" size="lg" className="w-full gap-2 rounded-xl">
                <Send className="h-4 w-4" /> {isAr ? "إرسال" : "Send message"}
              </Button>
            </form>
          </div>
        </div>
      </section>
    </Layout>
  );
}
