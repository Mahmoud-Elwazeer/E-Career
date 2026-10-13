import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Link } from "react-router-dom";

// Only these URL schemes are ever rendered as a clickable href. Anything else
// (javascript:, data:, vbscript:, etc.) is neutralized to "#" with the link
// text still shown as plain text — belt-and-suspenders on top of the fact
// that react-markdown (no rehype-raw configured) already renders embedded
// raw HTML as inert text rather than executing it.
const SAFE_URL_PATTERN = /^(https?:|mailto:|tel:|\/|#)/i;

function sanitizeHref(href: string | undefined): string {
  if (!href) return "#";
  const trimmed = href.trim();
  return SAFE_URL_PATTERN.test(trimmed) ? trimmed : "#";
}

/**
 * Renders admin-authored legal Markdown safely. react-markdown parses to React
 * elements (no `dangerouslySetInnerHTML`, no `rehype-raw`), so raw HTML
 * embedded in the source is rendered as inert text, not executed — this is
 * the XSS guard the directive requires for admin-rendered legal text. Link
 * hrefs are additionally restricted to an allowlist of safe schemes (http(s),
 * mailto, tel, relative, anchor) so a `javascript:`/`data:` URL in the
 * markdown source can never execute on click. Internal links (`/legal/...`,
 * `/app/...`) use the router's <Link> instead of a full page reload;
 * everything else opens in a new tab with `rel="noopener noreferrer"`.
 */
export function PolicyMarkdown({ content }: { content: string }) {
  return (
    <div className="prose prose-slate dark:prose-invert max-w-none prose-headings:font-display prose-a:text-primary">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children, ...props }) => {
            const safeHref = sanitizeHref(href);
            if (safeHref.startsWith("/")) {
              return <Link to={safeHref}>{children}</Link>;
            }
            return (
              <a href={safeHref} target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            );
          },
          img: ({ src, alt }) => {
            // Images follow the same scheme allowlist — no javascript:/data:
            // src can be used to smuggle a script via an image handler.
            const safeSrc = typeof src === "string" && /^https?:\/\//i.test(src) ? src : "";
            if (!safeSrc) return null;
            return <img src={safeSrc} alt={alt ?? ""} loading="lazy" />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
