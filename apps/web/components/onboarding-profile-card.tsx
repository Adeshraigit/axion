"use client";

import { useEffect, useState } from "react";

import { getProfile, updateProfile, uploadResumePdf } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type OnboardingProfileCardProps = {
  userId: string;
};

type ProfileResponse = {
  full_name?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  resume_text?: string | null;
  resume_file_name?: string | null;
  onboarding_completed_at?: string | null;
};

export function OnboardingProfileCard({ userId }: OnboardingProfileCardProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);

  const [fullName, setFullName] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [github, setGithub] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);

  useEffect(() => {
    getProfile(userId)
      .then((data) => {
        setProfile(data);
        setFullName(data.full_name ?? "");
        setLinkedin(data.linkedin_url ?? "");
        setGithub(data.github_url ?? "");
        setResumeUploaded(Boolean(data.resume_text));
      })
      .catch(() => {
        setError("Unable to load profile right now.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [userId]);

  const alreadyCompleted = Boolean(profile?.onboarding_completed_at);
  if (loading || dismissed || alreadyCompleted) {
    return null;
  }

  const onSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (resumeFile) {
        await uploadResumePdf(userId, resumeFile);
        setResumeUploaded(true);
      }

      const updated = await updateProfile(userId, {
        full_name: fullName,
        linkedin_url: linkedin,
        github_url: github,
        mark_onboarding_complete: true,
      });
      setProfile(updated);
    } catch {
      setError("Could not save profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="mb-5">
      <CardHeader>
        <div className="mb-2 flex items-center gap-2">
          <Badge variant="accent">First-time setup</Badge>
          <Badge variant="muted">Optional</Badge>
        </div>
        <CardTitle>Add your LinkedIn, GitHub, and resume</CardTitle>
        <CardDescription>
          This helps the mentor personalize memory context and job recommendations. You can skip and continue chatting.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input placeholder="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
        <Input
          placeholder="LinkedIn URL"
          value={linkedin}
          onChange={(event) => setLinkedin(event.target.value)}
        />
        <Input placeholder="GitHub URL" value={github} onChange={(event) => setGithub(event.target.value)} />
        <Input
          type="file"
          accept="application/pdf"
          onChange={(event) => {
            const selected = event.target.files?.[0] ?? null;
            setResumeFile(selected);
          }}
        />
        <p className="text-xs text-[#A1A1AA]">
          {resumeFile
            ? `Selected: ${resumeFile.name}`
            : resumeUploaded
              ? `Resume PDF uploaded${profile?.resume_file_name ? `: ${profile.resume_file_name}` : ""}`
              : "Upload your resume in PDF format"}
        </p>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={onSave} disabled={saving}>
            {saving ? "Saving..." : "Save details"}
          </Button>
          <Button variant="secondary" onClick={() => setDismissed(true)} disabled={saving}>
            Skip for now
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
