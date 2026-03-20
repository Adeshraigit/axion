"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";

type AppNavbarProps = {
  isLoggedIn: boolean;
  onSignOut?: () => void | Promise<void>;
};

export function AppNavbar({ isLoggedIn, onSignOut }: AppNavbarProps) {
  const pathname = usePathname();

  const links = [
    { label: "Home", href: "/" },
    ...(isLoggedIn
      ? [
          { label: "Chat", href: "/chat" },
          { label: "Dashboard", href: "/dashboard" },
        ]
      : []),
  ];

  return (
    <header className="flex items-center justify-between py-6 sm:py-8">
      <div className="flex items-center gap-2.5">
        <span className="text-lg font-bold tracking-tight">Axion</span>
      </div>

      <nav className="hidden items-center gap-8 md:flex">
        {links.map((item) => {
          const active = item.href !== "#" && pathname === item.href;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={
                active
                  ? "text-sm text-[#E5E5E5] underline underline-offset-8 decoration-[#F59E0B]"
                  : "text-sm text-[#A1A1AA] transition hover:text-[#E5E5E5]"
              }
            >
              {item.label}
            </Link>
          );
        })}

        {isLoggedIn ? (
          <Button variant="ghost" onClick={onSignOut}>
            Sign Out
          </Button>
        ) : (
          <Link href="/chat">
            <Button variant="secondary">Sign In</Button>
          </Link>
        )}
      </nav>
    </header>
  );
}
