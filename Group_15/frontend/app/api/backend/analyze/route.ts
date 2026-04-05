import { NextRequest, NextResponse } from "next/server";
import {
  fetchFromBackend,
  formatBackendUnreachableDetail,
  getServerBackendOrigins,
} from "@/lib/backendProxyFetch";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const origins = getServerBackendOrigins();

  let res: Response;
  try {
    const { response } = await fetchFromBackend("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    res = response;
  } catch (e) {
    return NextResponse.json(
      { detail: formatBackendUnreachableDetail(origins, e) },
      { status: 502 }
    );
  }

  if (!res.ok) {
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("content-type") ?? "application/json",
      },
    });
  }

  return new NextResponse(res.body, {
    status: 200,
    headers: {
      "Content-Type": res.headers.get("Content-Type") ?? "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
    },
  });
}
