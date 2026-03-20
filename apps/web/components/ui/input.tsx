import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-11 w-full rounded-xl border border-[#1F1F1F] bg-[#090909] px-3 text-sm text-[#E5E5E5] placeholder:text-[#6B7280] outline-none transition focus:border-[#F59E0B]/50 focus:ring-2 focus:ring-[#F59E0B]/20",
          className,
        )}
        {...props}
      />
    );
  },
);

Input.displayName = "Input";
