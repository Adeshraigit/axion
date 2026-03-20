"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown } from "lucide-react";

import { AppNavbar } from "@/components/app-navbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
// import { Card, CardContent } from "@/components/ui/card";

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const supabase = getSupabaseClient();
    if (!supabase || !isSupabaseConfigured()) {
      setIsLoggedIn(false);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setIsLoggedIn(Boolean(data.session?.user));
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_, session) => {
      setIsLoggedIn(Boolean(session?.user));
    });

    return () => {
      subscription.subscription.unsubscribe();
    };
  }, []);

  const handleSignOut = async () => {
    const supabase = getSupabaseClient();
    if (!supabase) {
      return;
    }
    await supabase.auth.signOut();
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#050505] text-[#E5E5E5]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(245,158,11,0.15),transparent_55%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(rgba(245,158,11,0.06)_1px,transparent_1px)] [background-size:36px_36px] opacity-40" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 sm:px-8">
        <AppNavbar isLoggedIn={isLoggedIn} onSignOut={handleSignOut} />

        <section className="relative mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center pb-20 text-center animate-fade-in-up">
          <Badge variant="muted" className="mb-5">
            Persistent AI career agent, not a one-off chat
          </Badge>

          <h1 className="text-[40px] font-extrabold leading-[1.12] tracking-[-0.03em] text-[#E5E5E5] sm:text-[52px] lg:text-[68px]">
            An AI agent that grows with you.
          </h1>

          <p className="mt-6 max-w-3xl text-base leading-7 text-[#A1A1AA] sm:text-lg">
            Track your skills, projects, and applications automatically.
            <br className="hidden sm:block" />
            Get 10 personalized job recommendations every day based on your progress, behavior, and goals.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <Badge variant="accent">Memory-first</Badge>
            <Badge variant="accent">Behavior analysis</Badge>
            <Badge variant="accent">Daily 10 role matches</Badge>
          </div>

          <div className="mt-10 flex w-full max-w-xl flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <Link href="/chat" className="w-full sm:w-auto">
              <Button size="large" className="w-full sm:w-auto">
                Start building your career
              </Button>
            </Link>
            <Link href="/dashboard" className="w-full sm:w-auto">
              <Button variant="secondary" size="large" className="w-full sm:w-auto">
                See how it works <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* <Card className="pointer-events-none absolute -right-2 top-[62%] hidden w-72 xl:block">
            <CardContent className="p-4 text-left">
              <p className="text-xs text-[#6B7280]">Today’s 10 job matches</p>
              <p className="mt-1 text-sm font-semibold text-[#E5E5E5]">Frontend Engineer Intern · 93% match</p>
              <div className="my-3 h-px bg-[#1F1F1F]" />
              <p className="text-xs text-[#6B7280]">Skill gap detected</p>
              <p className="mt-1 text-sm text-[#E5E5E5]">TypeScript system design depth</p>
            </CardContent>
          </Card> */}
        </section>

        <div className="pb-7 text-center">
          <ChevronDown className="mx-auto h-5 w-5 text-[#6B7280] animate-subtle-bounce" />
        </div>
      </div>
    </main>
  );
}
