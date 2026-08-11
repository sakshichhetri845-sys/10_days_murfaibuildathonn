import { NextResponse } from 'next/server';

export async function GET() {
  try {
    try {
      const backendRes = await fetch('http://127.0.0.1:8000/api/outbound/history');
      if (backendRes.ok) {
        const data = await backendRes.json();
        return NextResponse.json(data);
      }
    } catch (e) {
      console.warn(
        '[History API Proxy Warning]: Backend API server not reachable, executing local fallback',
        e
      );
    }

    const defaultHistory = [
      {
        callId: 'call_demo_01',
        maskedPhoneNumber: 'voi***',
        scheduledTime: new Date(Date.now() - 3600000).toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        status: 'completed',
        createdAt: new Date(Date.now() - 3600000).toISOString(),
      },
    ];

    return NextResponse.json({
      success: true,
      history: defaultHistory,
    });
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : 'Failed to fetch call history';
    return NextResponse.json({ success: false, error: errMessage }, { status: 500 });
  }
}
