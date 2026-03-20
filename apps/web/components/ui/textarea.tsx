import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-24 w-full rounded-xl border border-[#1F1F1F] bg-[#090909] px-3 py-2.5 text-sm text-[#E5E5E5] placeholder:text-[#6B7280] outline-none transition focus:border-[#F59E0B]/50 focus:ring-2 focus:ring-[#F59E0B]/20",
          className,
        )}
        {...props}
      />
    );
  },
);

Textarea.displayName = "Textarea";
