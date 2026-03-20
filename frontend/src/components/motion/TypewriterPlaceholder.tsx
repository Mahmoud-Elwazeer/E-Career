import { useEffect, useState, useCallback, useRef } from "react";
import { useReducedMotion } from "framer-motion";

interface TypewriterPlaceholderProps {
  /** Phrases to cycle through */
  phrases: string[];
  /** Typing speed in ms per unit (char for Latin, word for Arabic) */
  typeSpeed?: number;
  /** Delete speed in ms per unit */
  deleteSpeed?: number;
  /** Pause at full phrase in ms */
  pauseDuration?: number;
  /** CSS class for the container */
  className?: string;
}

/** Detect Arabic script */
function isArabicText(text: string): boolean {
  return /[\u0600-\u06FF]/.test(text);
}

/**
 * Typewriter placeholder effect that cycles through phrases.
 * Arabic: types word-by-word to preserve ligatures.
 * Latin: types character-by-character.
 * Reduced motion: shows static first phrase.
 */
export function TypewriterPlaceholder({
  phrases,
  typeSpeed = 60,
  deleteSpeed = 30,
  pauseDuration = 2000,
  className,
}: TypewriterPlaceholderProps) {
  const reduced = useReducedMotion();
  const [displayText, setDisplayText] = useState("");
  const [cursorVisible, setCursorVisible] = useState(true);
  const phraseIndex = useRef(0);
  const rafRef = useRef<number>();
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Cursor blink
  useEffect(() => {
    if (reduced) return;
    const interval = setInterval(() => setCursorVisible((v) => !v), 500);
    return () => clearInterval(interval);
  }, [reduced]);

  const typePhrase = useCallback(() => {
    const phrase = phrases[phraseIndex.current % phrases.length];
    const isArabic = isArabicText(phrase);

    // For Arabic: split into words. For Latin: split into chars.
    const units = isArabic ? phrase.split(/\s+/) : phrase.split("");
    let unitIndex = 0;

    function typeNext() {
      if (unitIndex <= units.length) {
        const built = isArabic
          ? units.slice(0, unitIndex).join(" ")
          : units.slice(0, unitIndex).join("");
        setDisplayText(built);
        unitIndex++;
        timeoutRef.current = setTimeout(typeNext, isArabic ? typeSpeed * 2.5 : typeSpeed);
      } else {
        // Pause then delete
        timeoutRef.current = setTimeout(deletePhrase, pauseDuration);
      }
    }

    function deletePhrase() {
      let currentLen = isArabic
        ? phrase.split(/\s+/).length
        : phrase.length;

      function deleteNext() {
        if (currentLen > 0) {
          currentLen--;
          const units2 = isArabic ? phrase.split(/\s+/) : phrase.split("");
          const built = isArabic
            ? units2.slice(0, currentLen).join(" ")
            : units2.slice(0, currentLen).join("");
          setDisplayText(built);
          timeoutRef.current = setTimeout(deleteNext, isArabic ? deleteSpeed * 2 : deleteSpeed);
        } else {
          setDisplayText("");
          phraseIndex.current++;
          timeoutRef.current = setTimeout(typePhrase, 300);
        }
      }

      deleteNext();
    }

    typeNext();
  }, [phrases, typeSpeed, deleteSpeed, pauseDuration]);

  useEffect(() => {
    if (reduced) {
      setDisplayText(phrases[0] || "");
      return;
    }

    // Start after initial delay
    timeoutRef.current = setTimeout(typePhrase, 1000);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [reduced, typePhrase, phrases]);

  if (reduced) {
    return <span className={className}>{phrases[0]}</span>;
  }

  return (
    <span className={className} aria-label={phrases[0]}>
      {displayText}
      <span
        className="inline-block w-[2px] h-[1.1em] bg-current align-text-bottom ms-0.5"
        style={{ opacity: cursorVisible ? 0.7 : 0 }}
        aria-hidden="true"
      />
    </span>
  );
}
