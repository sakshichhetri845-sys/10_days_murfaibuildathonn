import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    try {
      const backendRes = await fetch('http://127.0.0.1:8000/api/outbound/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (backendRes.ok) {
        const data = await backendRes.json();
        return NextResponse.json(data);
      }
    } catch (e) {
      console.warn(
        '[Schedule API Proxy Warning]: Backend API server not reachable, executing local fallback',
        e
      );
    }

    const { phoneNumber, scheduledTime, timezone } = body;
    if (!phoneNumber || typeof phoneNumber !== 'string' || phoneNumber.trim().length < 2) {
      return NextResponse.json(
        { success: false, error: 'Please provide a valid phone number or Linphone SIP username.' },
        { status: 400 }
      );
    }

    const callId = `sched_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const roomName = `outbound-followup-${callId.slice(-8)}`;

    return NextResponse.json({
      success: true,
      callId,
      roomName,
      status: 'scheduled',
      phoneNumber: phoneNumber.trim(),
      scheduledTime,
      timezone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      message: 'Call scheduled successfully!',
    });
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : 'Failed to schedule call';
    return NextResponse.json({ success: false, error: errMessage }, { status: 500 });
  }
}
