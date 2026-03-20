import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest, context: { params: Promise<{ userId: string }> }) {
  const { userId } = await context.params;
  const authorization = request.headers.get("authorization");
  const response = await fetch(`${BACKEND_URL}/api/v1/dashboard/${userId}`, {
    method: "GET",
    headers: {
      ...(authorization ? { Authorization: authorization } : {}),
    },
    cache: "no-store",
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
