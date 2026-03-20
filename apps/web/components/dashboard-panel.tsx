"use client";

import { useEffect, useState } from "react";
import { Activity, Briefcase, Sparkles, TrendingUp } from "lucide-react";

import { getDashboard } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type DashboardPanelProps = {
  userId: string;
};

type Skill = {
  name: string;
  level: number;
};

type JobRecommendation = {
  title: string;
  company: string;
  match_score: number;
  reasoning: string;
  expected_skills: string[];
  missing_skills: string[];
  profile_match: string;
};

type DashboardData = {
  profile: {
    full_name: string | null;
    linkedin_url: string | null;
    github_url: string | null;
    resume_text: string | null;
    resume_file_name: string | null;
    resume_uploaded_at: string | null;
    hindsight_synced_at: string | null;
  };
  skills: Skill[];
  applications_summary: {
    applied: number;
    interview: number;
    rejected: number;
    offer: number;
  };
  daily_recommendations: JobRecommendation[];
};

export function DashboardPanel({ userId }: DashboardPanelProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    getDashboard(userId)
      .then((nextData) => {
        setData(nextData);
      })
      .catch(() => {
        setData(null);
        setError("Unable to load dashboard data. Please refresh or sign in again.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [userId]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-[#F59E0B]" /> Career Dashboard
          </CardTitle>
          <CardDescription>Track momentum, close skill gaps, and focus on roles that match your trajectory.</CardDescription>
        </CardHeader>
      </Card>

      {isLoading ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-[#A1A1AA]">Loading dashboard...</CardContent>
        </Card>
      ) : error || !data ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-red-400">
            {error ?? "No dashboard data available yet."}
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Profile context</CardTitle>
              <CardDescription>Used by memory + recommendations personalization</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-[#A1A1AA]">
              <p>
                Name: <span className="text-[#E5E5E5]">{data.profile.full_name || "Not provided"}</span>
              </p>
              <p>
                LinkedIn: <span className="text-[#E5E5E5]">{data.profile.linkedin_url || "Not provided"}</span>
              </p>
              <p>
                GitHub: <span className="text-[#E5E5E5]">{data.profile.github_url || "Not provided"}</span>
              </p>
              <p className="max-h-20 overflow-hidden">
                Resume: <span className="text-[#E5E5E5]">{data.profile.resume_text || "Not provided"}</span>
              </p>
              {data.profile.resume_file_name && (
                <div className="pt-1">
                  <Badge variant="accent">Resume uploaded: {data.profile.resume_file_name}</Badge>
                </div>
              )}
              {data.profile.hindsight_synced_at && (
                <p>
                  Hindsight sync: <span className="text-[#E5E5E5]">{new Date(data.profile.hindsight_synced_at).toLocaleString()}</span>
                </p>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Applied" value={data.applications_summary.applied} />
            <MetricCard label="Interview" value={data.applications_summary.interview} />
            <MetricCard label="Offer" value={data.applications_summary.offer} />
            <MetricCard label="Rejected" value={data.applications_summary.rejected} />
          </div>

          <div className="grid gap-4 xl:grid-cols-5">
            <Card className="xl:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <TrendingUp className="h-4 w-4 text-[#F59E0B]" /> Skills
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.skills.map((skill: Skill) => (
                  <div key={skill.name}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span>{skill.name}</span>
                      <span className="text-[#A1A1AA]">Level {skill.level}</span>
                    </div>
                    <div className="h-2 rounded-full bg-[#131313]">
                      <div className="h-2 rounded-full bg-[#F59E0B]" style={{ width: `${Math.min(100, skill.level * 20)}%` }} />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="xl:col-span-3">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Briefcase className="h-4 w-4 text-[#F59E0B]" /> Daily Job Suggestions (10)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.daily_recommendations.length === 0 && (
                  <p className="text-sm text-[#A1A1AA]">No recommendations yet. Keep chatting so the agent can personalize better.</p>
                )}
                {data.daily_recommendations.map((job: JobRecommendation) => (
                  <div key={`${job.company}-${job.title}`} className="rounded-xl border border-[#1F1F1F] bg-[#111111] p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-[#E5E5E5]">{job.title}</p>
                      <Badge variant="accent">{job.match_score}%</Badge>
                    </div>
                    <p className="text-xs text-[#A1A1AA]">{job.company}</p>
                    <p className="mt-2 text-xs text-[#E5E5E5]">{job.profile_match}</p>
                    {!!job.expected_skills?.length && (
                      <p className="mt-1 text-xs text-[#A1A1AA]">Expected: {job.expected_skills.join(", ")}</p>
                    )}
                    {!!job.missing_skills?.length && (
                      <p className="mt-1 text-xs text-red-400">You lack: {job.missing_skills.join(", ")}</p>
                    )}
                    <p className="mt-2 text-xs leading-5 text-[#A1A1AA]">{job.reasoning}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-wide text-[#A1A1AA]">{label}</p>
          <Sparkles className="h-3.5 w-3.5 text-[#F59E0B]" />
        </div>
        <p className="mt-2 text-2xl font-bold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  );
}
