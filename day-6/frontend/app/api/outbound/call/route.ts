import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { phoneNumber, userId } = body;

    if (!phoneNumber || typeof phoneNumber !== 'string' || phoneNumber.trim().length < 2) {
      return NextResponse.json(
        { success: false, error: 'Please provide a valid phone number or Linphone SIP username.' },
        { status: 400 }
      );
    }

    // Try forwarding to Python Backend HTTP API Server (http://127.0.0.1:8000/api/outbound/call)
    try {
      const backendRes = await fetch('http://127.0.0.1:8000/api/outbound/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phoneNumber, userId: userId || 'riya_verma' }),
      });

      const data = await backendRes.json();
      return NextResponse.json(data, { status: backendRes.status });
    } catch (backendErr) {
      console.warn(
        '[Call API Proxy Warning]: Backend API server not reachable, executing local fallback',
        backendErr
      );
    }

    // Local Fallback Execution via LiveKit Server SDK
    const cleanedPhone = phoneNumber.trim();
    const livekitUrl = process.env.LIVEKIT_URL || '';
    const apiKey = process.env.LIVEKIT_API_KEY || '';
    const apiSecret = process.env.LIVEKIT_API_SECRET || '';
    const trunkId =
      process.env.LIVEKIT_SIP_OUTBOUND_TRUNK_ID || process.env.LIVEKIT_SIP_TRUNK_ID || '';

    const callId = `call_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const roomName = `outbound-followup-${callId.slice(-8)}`;

    if (!apiKey || !apiSecret || !trunkId) {
      return NextResponse.json(
        {
          success: false,
          error:
            'LiveKit SIP trunk credentials (LIVEKIT_SIP_OUTBOUND_TRUNK_ID) not fully configured.',
          callId,
          roomName,
          status: 'failed',
        },
        { status: 500 }
      );
    }

    const { SipClient } = await import('livekit-server-sdk');
    const httpUrl = livekitUrl.replace('wss://', 'https://').replace('ws://', 'http://');
    const sipClient = new SipClient(httpUrl, apiKey, apiSecret);

    const participant = await sipClient.createSipParticipant(trunkId, cleanedPhone, roomName, {
      participantIdentity: `sip_user_${callId.slice(-6)}`,
      participantName: `HealthSaathi Caller (${cleanedPhone})`,
      playDialtone: true,
    });

    return NextResponse.json({
      success: true,
      callId,
      roomName,
      status: 'calling',
      participantId: participant.participantId || callId,

      message: 'Outbound call initiated successfully!',
    });
  } catch (err: unknown) {
    console.error('[Outbound API Error]:', err);
    const errMessage = err instanceof Error ? err.message : 'Failed to dispatch outbound call';
    return NextResponse.json(
      {
        success: false,
        error: errMessage,
        status: 'failed',
      },
      { status: 500 }
    );
  }
}
