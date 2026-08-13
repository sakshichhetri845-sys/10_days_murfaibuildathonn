import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export const revalidate = 0;

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const range = searchParams.get('range') || 'all';

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys, json; sys.path.append('src'); from db import get_call_analytics; res = get_call_analytics(range_filter='${range}'); print(json.dumps(res))`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 5000,
    });

    const data = JSON.parse(stdout.trim() || '{}');

    const analytics = {
      totalCalls: data.total_calls ?? 0,
      successfulCalls: data.successful_calls ?? 0,
      failedCalls: data.failed_calls ?? 0,
      successRate: data.success_rate ?? 0.0,
      outcomeBreakdown: data.outcome_breakdown ?? {
        GENERAL_GUIDANCE: 0,
        TRIAGE_COMPLETED: 0,
        FACILITY_FOUND: 0,
        HUMAN_ESCALATION: 0,
        INCOMPLETE: 0,
        TECHNICAL_ERROR: 0,
      },
      recentCalls: (data.recent_calls || []).map((c: Record<string, unknown>) => ({
        id: (c.id as string) || '',
        sessionId: (c.session_id as string) || '',
        timestamp: (c.timestamp as string) || '',
        duration: (c.duration as number) ?? 0,
        channel: (c.channel as string) ?? 'browser',
        outcome: (c.outcome as string) ?? 'failed',
        outcomeType: (c.outcome_type as string) ?? 'INCOMPLETE',
      })),
    };

    return NextResponse.json({ success: true, analytics });
  } catch (err) {
    console.warn('Analytics API GET warning:', err);
    return NextResponse.json(
      {
        success: false,
        analytics: {
          totalCalls: 0,
          successfulCalls: 0,
          failedCalls: 0,
          successRate: 0.0,
          outcomeBreakdown: {
            GENERAL_GUIDANCE: 0,
            TRIAGE_COMPLETED: 0,
            FACILITY_FOUND: 0,
            HUMAN_ESCALATION: 0,
            INCOMPLETE: 0,
            TECHNICAL_ERROR: 0,
          },
          recentCalls: [],
        },
      },
      { status: 200 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const {
      sessionId,
      duration = 0,
      channel = 'browser',
      outcome = 'failed',
      outcomeType = 'INCOMPLETE',
    } = body;

    if (!sessionId) {
      return NextResponse.json({ success: false, error: 'Missing sessionId' }, { status: 400 });
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys, json; sys.path.append('src'); from db import save_call_analytics; res = save_call_analytics(session_id='${sessionId}', duration=${Number(duration)}, channel='${channel}', outcome='${outcome}', outcome_type='${outcomeType}'); print(json.dumps(res))`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 5000,
    });

    const res = JSON.parse(stdout.trim() || '{}');
    return NextResponse.json({ success: true, record: res });
  } catch (err) {
    console.warn('Analytics API POST warning:', err);
    return NextResponse.json({ success: false, error: String(err) }, { status: 500 });
  }
}
