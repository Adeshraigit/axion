"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type AuthGateProps = {
  children: (auth: { userId: string; email: string | null; signOut: () => Promise<void> }) => React.ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const supabase = getSupabaseClient();
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      if (data.session?.access_token) {
        localStorage.setItem("supabase_access_token", data.session.access_token);
      }
      if (data.session?.user?.id) {
        localStorage.setItem("supabase_user_id", data.session.user.id);
      }
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_, nextSession) => {
      setSession(nextSession);
      if (nextSession?.access_token) {
        localStorage.setItem("supabase_access_token", nextSession.access_token);
      } else {
        localStorage.removeItem("supabase_access_token");
      }

      if (nextSession?.user?.id) {
        localStorage.setItem("supabase_user_id", nextSession.user.id);
      } else {
        localStorage.removeItem("supabase_user_id");
      }
    });

    return () => {
      subscription.subscription.unsubscribe();
    };
  }, [supabase]);

  if (!isSupabaseConfigured()) {
    return (
      <div className="mx-auto mt-16 max-w-md px-6">
        <Card>
          <CardHeader>
            <CardTitle>Supabase Auth not configured</CardTitle>
            <CardDescription>
              Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in apps/web/.env.local and restart.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const onSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      if (!supabase) {
        throw new Error("Supabase client not initialized");
      }
      if (mode === "signin") {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
      } else {
        const { error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) throw signUpError;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    if (!supabase) {
      return;
    }
    await supabase.auth.signOut();
  };

  if (!session?.user) {
    return (
      <div className="min-h-screen bg-[#050505] px-6 py-16 text-[#E5E5E5]">
        <div className="mx-auto max-w-md">
          <Card>
            <CardHeader>
              <div className="mb-2 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#F59E0B]" />
                <Badge variant="accent">Secure Sign-In</Badge>
              </div>
              <CardTitle>{mode === "signin" ? "Welcome back" : "Create your account"}</CardTitle>
              <CardDescription>Use Supabase Auth to continue into your persistent AI career workspace.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />

              {error && <p className="text-sm text-red-400">{error}</p>}

              <Button onClick={onSubmit} disabled={loading} className="w-full">
                {loading ? "Please wait..." : mode === "signin" ? "Sign In" : "Sign Up"}
              </Button>

              <Button
                onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
                variant="secondary"
                className="w-full"
              >
                {mode === "signin" ? "Create new account" : "Already have an account? Sign in"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return <>{children({ userId: session.user.id, email: session.user.email ?? null, signOut })}</>;
}
