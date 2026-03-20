import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "default" | "large";
};

const base =
  "inline-flex items-center justify-center whitespace-nowrap rounded-full font-medium transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F59E0B]/40 disabled:pointer-events-none disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]";

const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-[#F59E0B] text-white shadow-[0_0_36px_rgba(245,158,11,0.15)] hover:bg-[#D97706] hover:brightness-110",
  secondary: "border border-[#1F1F1F] bg-transparent text-[#A1A1AA] hover:border-[#2A2A2A] hover:text-[#E5E5E5] hover:brightness-110",
  ghost: "bg-transparent text-[#A1A1AA] hover:text-[#E5E5E5]",
};

const sizes: Record<NonNullable<ButtonProps["size"]>, string> = {
  default: "px-6 py-3 text-sm",
  large: "px-8 py-4 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", ...props }, ref) => {
    return <button ref={ref} className={cn(base, variants[variant], sizes[size], className)} {...props} />;
  },
);

Button.displayName = "Button";
