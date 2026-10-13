import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Link } from "react-router-dom";

/**
 * Renders admin-authored legal Markdown safely. react-markdown parses to React
 * elements (no `dangerouslySetInnerHTML`), so raw HTML embedded in the source
 * is NOT executed — this is the XSS guard the directive requires for
 * admin-rendered legal text. Internal links (`/legal/...`, `/app/...`) use the
 * router's <Link> instead of a full page reload; everything else opens in a
 * new tab with `rel="noopener noreferrer"`.
 */
export function PolicyMarkdown({ content }: { content: string }) {
  return (
    <div className="prose prose-slate dark:prose-invert max-w-none prose-headings:font-display prose-a:text-primary">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children, ...props }) => {
            if (href && href.startsWith("/")) {
              return <Link to={href}>{children}</Link>;
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
