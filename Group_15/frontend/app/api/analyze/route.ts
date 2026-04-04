import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { idea_description, audience, product_url } = body;

    if (!idea_description) {
      return NextResponse.json(
        { error: "idea_description is required" },
        { status: 400 }
      );
    }

    const id = randomUUID();

    return NextResponse.json({ id });
  } catch (error) {
    return NextResponse.json(
      { error: "Invalid request" },
      { status: 400 }
    );
  }
}
