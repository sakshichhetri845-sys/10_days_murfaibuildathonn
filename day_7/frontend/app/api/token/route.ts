import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME?.trim() || 'my-agent';

// don't cache the results
export const revalidate = 0;

async function getOrGenerateUserId(
  req: Request,
  body?: Record<string, unknown>
): Promise<{ userId: string; isNewCookie: boolean }> {
  const url = new URL(req.url);
  const queryUserId = url.searchParams.get('userId') || url.searchParams.get('user_id');
  const bodyUserId = (body?.userId as string | undefined) || (body?.user_id as string | undefined);

  if (queryUserId) {
    return { userId: queryUserId, isNewCookie: false };
  }
  if (bodyUserId) {
    return { userId: bodyUserId, isNewCookie: false };
  }

  try {
    const cookieStore = await cookies();
    const cookieUserId = cookieStore.get('bolbuddy_user_id')?.value;
    if (cookieUserId) {
      return { userId: cookieUserId, isNewCookie: false };
    }
  } catch {
    // Ignore cookie retrieval errors in static contexts
  }

  const newUserId = `bolbuddy_user_${Math.random().toString(36).substring(2, 10)}${Date.now().toString(36)}`;
  return { userId: newUserId, isNewCookie: true };
}

async function handleTokenRequest(req: Request, body?: Record<string, unknown>) {
  if (LIVEKIT_URL === undefined) {
    throw new Error('LIVEKIT_URL is not defined');
  }
  if (API_KEY === undefined) {
    throw new Error('LIVEKIT_API_KEY is not defined');
  }
  if (API_SECRET === undefined) {
    throw new Error('LIVEKIT_API_SECRET is not defined');
  }

  let roomConfig: RoomConfiguration | undefined;
  if (body?.room_config) {
    roomConfig = RoomConfiguration.fromJson(
      body.room_config as Parameters<typeof RoomConfiguration.fromJson>[0],
      { ignoreUnknownFields: true }
    );
  } else if (AGENT_NAME) {
    roomConfig = RoomConfiguration.fromJson(
      { agents: [{ agentName: AGENT_NAME }] },
      { ignoreUnknownFields: true }
    );
  }

  const { userId, isNewCookie } = await getOrGenerateUserId(req, body);
  const participantName = typeof body?.participantName === 'string' ? body.participantName : 'user';
  const participantIdentity = userId;
  const sessionNonce = Math.random().toString(36).substring(2, 7);
  const roomName =
    (body?.roomName as string | undefined) ||
    `bolbuddy_room_${userId.replace(/[^a-zA-Z0-9_-]/g, '_')}_${sessionNonce}`;

  const participantToken = await createParticipantToken(
    { identity: participantIdentity, name: participantName },
    roomName,
    roomConfig
  );

  const data: ConnectionDetails = {
    serverUrl: LIVEKIT_URL,
    roomName,
    participantName,
    participantToken,
  };

  const response = NextResponse.json(data, {
    headers: {
      'Cache-Control': 'no-store',
    },
  });

  if (isNewCookie) {
    response.cookies.set('bolbuddy_user_id', userId, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365, // 1 year persistence
      sameSite: 'lax',
      httpOnly: true,
    });
  }

  return response;
}

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    return await handleTokenRequest(req, body);
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

export async function GET(req: Request) {
  try {
    return await handleTokenRequest(req);
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}
