"use client";

import Link from "next/link";
import { LogOut } from "lucide-react";

import { AuthGate } from "@/components/auth-gate";
import { ChatPanel } from "@/components/chat-panel";
import { DashboardPanel } from "@/components/dashboard-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function HomeShell() {
  return (
    <AuthGate>
      {({ userId, email, signOut }) => (
        <main className="min-h-screen bg-[#050505] text-[#E5E5E5]">
          <div className="mx-auto max-w-7xl px-6 py-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <h1 className="text-3xl font-bold tracking-tight">Axion Workspace</h1>
              <p className="mt-2 text-[#A1A1AA]">
                Personalized career guidance with memory, application tracking, daily job recommendations, and voice support.
              </p>
              <div className="flex flex-wrap gap-2">
                <Link href="/chat"><Badge variant="accent">Chat</Badge></Link>
                <Link href="/dashboard"><Badge variant="muted">Dashboard</Badge></Link>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="muted">Signed in as: {email ?? userId}</Badge>
                <Badge variant="accent">Persistent AI Agent</Badge>
              </div>
            </div>
            <Button onClick={signOut} variant="secondary">
              <LogOut className="mr-2 h-4 w-4" /> Sign out
            </Button>
          </div>

            <section className="mt-6 grid gap-6 lg:grid-cols-12">
              <div className="lg:col-span-5">
                <ChatPanel userId={userId} />
              </div>
              <div className="lg:col-span-7">
                <DashboardPanel userId={userId} />
              </div>
            </section>
          </div>
        </main>
      )}
    </AuthGate>
  );
}
