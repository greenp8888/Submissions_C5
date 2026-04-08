import { NextRequest, NextResponse } from "next/server";
import {
  fetchFromBackend,
  formatBackendUnreachableDetail,
  getServerBackendOrigins,
} from "@/lib/backendProxyFetch";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const origins = getServerBackendOrigins();

  try {
    const { response: res } = await fetchFromBackend("/tagline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (e) {
    return NextResponse.json(
      { detail: formatBackendUnreachableDetail(origins, e) },
      { status: 502 }
    );
  }
}
