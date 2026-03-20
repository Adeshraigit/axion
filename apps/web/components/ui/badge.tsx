import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "muted" | "accent";
};

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants: Record<NonNullable<BadgeProps["variant"]>, string> = {
    default: "border border-[#1F1F1F] bg-[#101010] text-[#E5E5E5]",
    muted: "border border-[#1F1F1F] bg-transparent text-[#A1A1AA]",
    accent: "border border-[#2B1E07] bg-[rgba(245,158,11,0.12)] text-[#F59E0B]",
  };

  return (
    <span
      className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-medium", variants[variant], className)}
      {...props}
    />
  );
}
