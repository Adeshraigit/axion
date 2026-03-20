import Link from "next/link";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-[#050505] text-[#E5E5E5]">
      <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col items-center justify-center px-6 text-center">
        <div className="rounded-full border border-[#2B1E07] bg-[rgba(245,158,11,0.12)] p-3">
          <AlertCircle className="h-6 w-6 text-[#F59E0B]" />
        </div>

        <h1 className="mt-6 text-5xl font-extrabold tracking-tight sm:text-6xl">404</h1>
        <p className="mt-3 text-xl font-semibold tracking-tight">Page not found</p>
        <p className="mt-2 max-w-xl text-sm text-[#A1A1AA] sm:text-base">
          The page you are looking for does not exist or may have been moved. You can continue from one of the main
          sections below.
        </p>

        <div className="mt-8 flex w-full max-w-lg flex-col gap-3 sm:flex-row sm:justify-center">
          <Link href="/" className="w-full sm:w-auto">
            <Button className="w-full">Back to Home</Button>
          </Link>
          <Link href="/chat" className="w-full sm:w-auto">
            <Button variant="secondary" className="w-full">Open Chat</Button>
          </Link>
          <Link href="/dashboard" className="w-full sm:w-auto">
            <Button variant="secondary" className="w-full">Open Dashboard</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
