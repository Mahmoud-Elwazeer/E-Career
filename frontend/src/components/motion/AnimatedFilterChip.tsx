import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnimatedFilterChipProps {
  label: string;
  filterKey: string;
  onRemove: (key: string) => void;
}

export function AnimatedFilterChip({ label, filterKey, onRemove }: AnimatedFilterChipProps) {
  const reduced = useReducedMotion();

  return (
    <motion.button
      layout={!reduced}
      initial={reduced ? { opacity: 1 } : { opacity: 0, scale: 0.8, filter: "blur(4px)" }}
      animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
      exit={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.8, filter: "blur(4px)" }}
      transition={{
        layout: { type: "spring", stiffness: 400, damping: 28 },
        opacity: { duration: 0.2 },
        scale: { type: "spring", stiffness: 500, damping: 26 },
        filter: { duration: 0.15 },
      }}
      onClick={() => onRemove(filterKey)}
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium",
        "bg-secondary text-secondary-foreground",
        "hover:bg-destructive/10 hover:text-destructive",
        "transition-colors duration-150 cursor-pointer",
        "active:scale-95"
      )}
    >
      <span className="capitalize">{label}</span>
      <X className="h-3 w-3" />
    </motion.button>
  );
}

/**
 * Wrapper that handles AnimatePresence for a list of filter chips.
 */
export function AnimatedFilterChipList({
  filters,
  onRemove,
  onClearAll,
  clearLabel = "Clear all",
}: {
  filters: { key: string; label: string }[];
  onRemove: (key: string) => void;
  onClearAll: () => void;
  clearLabel?: string;
}) {
  return (
    <motion.div
      layout
      className="flex items-center gap-2 flex-wrap"
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
    >
      <AnimatePresence mode="popLayout">
        {filters.map((f) => (
          <AnimatedFilterChip
            key={f.key}
            filterKey={f.key}
            label={f.label}
            onRemove={onRemove}
          />
        ))}
      </AnimatePresence>
      {filters.length > 0 && (
        <button
          onClick={onClearAll}
          className="text-xs text-primary hover:underline transition-colors"
        >
          {clearLabel}
        </button>
      )}
    </motion.div>
  );
}
