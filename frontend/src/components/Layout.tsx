import { AuthNavbar } from "./AuthNavbar";
import { Footer } from "./Footer";
import { PageTransition } from "./motion";
import { LayoutGroup } from "framer-motion";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <LayoutGroup>
      <div className="min-h-screen flex flex-col">
        <AuthNavbar />
        <main id="main-content" className="flex-1">
          <PageTransition>{children}</PageTransition>
        </main>
        <Footer />
      </div>
    </LayoutGroup>
  );
}
