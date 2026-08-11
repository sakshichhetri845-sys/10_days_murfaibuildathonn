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
const AGENT_NAME = process.env.AGENT_NAME || 'my-agent';

// don't cache the results
export const revalidate = 0;

export async function GET(req: Request) {
  return handleTokenRequest(req);
}

export async function POST(req: Request) {
  return handleTokenRequest(req);
}

async function handleTokenRequest(req: Request) {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Parse room config and user_id from request
    const url = new URL(req.url);
    const searchUserId = url.searchParams.get('user_id');
    const headerUserId = req.headers.get('x-user-id');

    let body: Record<string, unknown> = {};
    if (req.method === 'POST') {
      body = (await req.json().catch(() => ({}))) as Record<string, unknown>;
    }

    const bodyUserId =
      typeof body?.user_id === 'string'
        ? body.user_id
        : typeof body?.userId === 'string'
          ? body.userId
          : undefined;

    let roomConfig: RoomConfiguration | undefined;
    if (body?.room_config) {
      roomConfig = RoomConfiguration.fromJson(
        body.room_config as unknown as Parameters<typeof RoomConfiguration.fromJson>[0],
        { ignoreUnknownFields: true }
      );
    } else if (AGENT_NAME) {
      roomConfig = RoomConfiguration.fromJson(
        { agents: [{ agentName: AGENT_NAME }] } as unknown as Parameters<
          typeof RoomConfiguration.fromJson
        >[0],
        { ignoreUnknownFields: true }
      );
    }

    // Generate participant token with stable user_id if provided
    const participantName = 'user';
    const participantIdentity =
      searchUserId ||
      bodyUserId ||
      headerUserId ||
      `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;

    // Room name includes a short random suffix so each browser session gets a
    // fresh room — prevents stale rooms from blocking new sessions.
    // The stable participantIdentity (user_id) is preserved for memory lookups.
    const sessionSuffix = Math.random().toString(36).substring(2, 7);
    const roomName = `healthsathi_${participantIdentity}_${sessionSuffix}`;

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName,
      roomConfig
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
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
