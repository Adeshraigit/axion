import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest, context: { params: Promise<{ userId: string }> }) {
  const { userId } = await context.params;
  const authorization = request.headers.get("authorization");
  const formData = await request.formData();

  const backendCandidates = [BACKEND_URL, "http://127.0.0.1:8000", "http://localhost:8000"];
  let lastError: unknown = null;

  for (const baseUrl of backendCandidates) {
    try {
      const response = await fetch(`${baseUrl}/api/v1/profile/${userId}/resume`, {
        method: "POST",
        headers: {
          ...(authorization ? { Authorization: authorization } : {}),
        },
        body: formData,
        cache: "no-store",
      });

      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
      }

      const text = await response.text();
      return NextResponse.json(
        {
          detail: text || "Unexpected backend response",
        },
        { status: response.status },
      );
    } catch (error) {
      lastError = error;
    }
  }

  return NextResponse.json(
    {
      detail: "Backend API is unreachable. Ensure FastAPI is running on port 8000 and BACKEND_URL is correct.",
      error: String(lastError ?? "unknown error"),
    },
    { status: 503 },
  );
}
