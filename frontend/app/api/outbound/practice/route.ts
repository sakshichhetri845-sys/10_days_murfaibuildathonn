import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const cookieStore = await cookies();
    const cookieUserId = cookieStore.get('bolbuddy_user_id')?.value;
    const userId = body.userId || body.user_id || cookieUserId || 'default_user';
    const phoneNumber = body.phoneNumber || body.phone_number || '';
    const scheduledTime = body.scheduledTime || body.scheduled_time || '20:00';
    const practiceTopic = body.practiceTopic || body.practice_topic || 'Spoken English Practice';
    const timezone = body.timezone || 'Asia/Kolkata';
    const action =
      body.action ||
      (body.cancel ? 'cancel_schedule' : body.immediate ? 'immediate' : 'save_schedule');
    const name = body.name || '';

    if (!userId) {
      return NextResponse.json({ success: false, error: 'userId is required' }, { status: 400 });
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    let pyScript = '';
    if (action === 'cancel_schedule') {
      pyScript = `import sys, json; sys.path.append('src'); from schedule_model import cancel_schedule; res = cancel_schedule(user_id='${userId}'); print(json.dumps({'success': res, 'cancelled': res}))`;
    } else if (action === 'immediate') {
      pyScript = `import sys, json, asyncio; sys.path.append('src'); from outbound import trigger_outbound_practice; res = asyncio.run(trigger_outbound_practice(user_id='${userId}', phone_number='${phoneNumber}', name='${name}')); print(json.dumps(res))`;
    } else {
      pyScript = `import sys, json; sys.path.append('src'); from schedule_model import create_or_update_schedule; res = create_or_update_schedule(user_id='${userId}', phone_number='${phoneNumber}', practice_topic='${practiceTopic}', preferred_time='${scheduledTime}', timezone='${timezone}'); print(json.dumps({'success': True, 'schedule': res}))`;
    }

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 10000,
    });

    const result = JSON.parse(stdout.trim() || '{}');
    return NextResponse.json(result);
  } catch (err: unknown) {
    console.error('Outbound practice API error:', err);
    return NextResponse.json(
      {
        success: false,
        error: (err as Error)?.message || 'Failed to process outbound call request',
      },
      { status: 500 }
    );
  }
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const cookieStore = await cookies();
    const cookieUserId = cookieStore.get('bolbuddy_user_id')?.value;
    const userId = searchParams.get('userId') || cookieUserId;

    if (!userId) {
      return NextResponse.json({ success: true, calls: [], schedule: null });
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys, json; sys.path.append('src'); from db import get_scheduled_calls; from schedule_model import get_schedule; from telephony import mask_phone_number; calls = get_scheduled_calls(user_id='${userId}'); formatted_calls = [{**c, 'phone_number': mask_phone_number(c.get('phone_number',''))} for c in calls]; sched = get_schedule(user_id='${userId}'); formatted_sched = {**sched, 'phone_number': mask_phone_number(sched.get('phone_number',''))} if sched else None; print(json.dumps({'calls': formatted_calls, 'schedule': formatted_sched}))`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 5000,
    });

    const data = JSON.parse(stdout.trim() || '{"calls":[], "schedule":null}');
    return NextResponse.json({ success: true, ...data });
  } catch (err: unknown) {
    console.warn('Outbound GET API error:', err);
    return NextResponse.json({ success: false, calls: [], schedule: null }, { status: 200 });
  }
}
