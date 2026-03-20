"use client";

import { LayoutDashboard, LogOut } from "lucide-react";

import { AppNavbar } from "@/components/app-navbar";
import { AuthGate } from "@/components/auth-gate";
import { DashboardPanel } from "@/components/dashboard-panel";
import { OnboardingProfileCard } from "@/components/onboarding-profile-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  return (
    <AuthGate>
      {({ userId, email, signOut }) => (
        <main className="min-h-screen bg-[#050505] text-[#E5E5E5]">
          <div className="mx-auto max-w-6xl px-6 py-8">
            <AppNavbar isLoggedIn onSignOut={signOut} />

            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-3">
                <h1 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                  <LayoutDashboard className="h-6 w-6 text-[#F59E0B]" /> Dashboard
                </h1>
                <Badge variant="accent">Progress and recommendations</Badge>
                <Badge variant="muted">Signed in as: {email ?? userId}</Badge>
              </div>

              <Button onClick={signOut} variant="secondary">
                <LogOut className="mr-2 h-4 w-4" /> Sign out
              </Button>
            </div>

            <OnboardingProfileCard userId={userId} />
            <DashboardPanel userId={userId} />
          </div>
        </main>
      )}
    </AuthGate>
  );
}
