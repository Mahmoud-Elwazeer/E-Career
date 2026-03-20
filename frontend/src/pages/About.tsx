import { Layout } from "@/components/Layout";
import { Target, Users, Zap, Globe } from "lucide-react";
import { usePageMeta } from "@/hooks/use-seo";

export default function About() {
  usePageMeta("About USAM", "Learn about USAM Jobs — the MENA job aggregator that brings opportunities from dozens of platforms into one search.");

  return (
    <Layout>
      <section className="us-watermark bg-primary text-primary-foreground py-16">
        <div className="container relative z-10 max-w-3xl text-center">
          <h1 className="text-3xl md:text-4xl font-medium mb-4">About USAM</h1>
          <p className="text-lg font-light opacity-80">
            One search. Every opportunity. We aggregate jobs from top platforms across MENA so you never miss a relevant posting.
          </p>
        </div>
      </section>

      <section className="container py-16 max-w-3xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
          {[
            { icon: Target, title: "Our Mission", desc: "To simplify the job search for Arab students and young professionals by aggregating opportunities from dozens of sources into one clean, filterable feed." },
            { icon: Users, title: "Who We Serve", desc: "Fresh graduates, career switchers, and remote workers across the MENA region looking for their next opportunity." },
            { icon: Zap, title: "Why USAM", desc: "No more tab overload. Search once, find everywhere. Save jobs, set alerts, and apply directly to the source." },
            { icon: Globe, title: "Our Reach", desc: "We aggregate from LinkedIn, Bayt, Wuzzuf, GulfTalent, and more — covering 10+ countries and 8 industries." },
          ].map((item) => (
            <div key={item.title} className="flex gap-4">
              <item.icon className="h-6 w-6 text-primary shrink-0 mt-1" />
              <div>
                <h3 className="font-medium mb-1">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </Layout>
  );
}
