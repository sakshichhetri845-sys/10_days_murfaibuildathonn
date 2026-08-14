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
    const cookieUserId = cookieStore.get('healthsathi_user_id')?.value;
    const userId = body.userId || cookieUserId || 'default_user';
    const phoneNumber = body.phoneNumber || '';
    const scheduledTime = body.scheduledTime || '08:00';
    const topic = body.topic || 'Health Reminder';
    const timezone = body.timezone || 'Asia/Kolkata';

    if (!phoneNumber) {
      return NextResponse.json(
        { success: false, error: 'Phone number is required' },
        { status: 400 }
      );
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys, json; from dotenv import load_dotenv; load_dotenv('.env.local'); sys.path.append('src'); from schedule_model import create_or_update_schedule; res = create_or_update_schedule(user_id='${userId}', phone_number='${phoneNumber}', practice_topic='${topic}', preferred_time='${scheduledTime}', timezone='${timezone}'); print(json.dumps({'success': True, 'schedule': res}))`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 10000,
    });

    const result = JSON.parse(stdout.trim() || '{}');
    return NextResponse.json(result);
  } catch (err: unknown) {
    console.error('Schedule reminder API error:', err);
    return NextResponse.json(
      {
        success: false,
        error: (err as Error)?.message || 'Failed to schedule reminder',
      },
      { status: 500 }
    );
  }
}
