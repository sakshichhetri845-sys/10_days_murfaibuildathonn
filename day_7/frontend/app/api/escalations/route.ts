import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const userId = searchParams.get('userId') || '';
    const status = searchParams.get('status') || '';

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys, json; sys.path.append('src'); from db import get_escalations; res = get_escalations(user_id='${userId}', status='${status}'); print(json.dumps(res))`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 5000,
    });

    const escalations = JSON.parse(stdout.trim() || '[]');
    return NextResponse.json({ success: true, escalations });
  } catch (err) {
    console.warn('Escalations API GET warning:', err);
    return NextResponse.json({ success: false, escalations: [] }, { status: 200 });
  }
}

export async function PATCH(req: Request) {
  try {
    const body = await req.json();
    const { referenceId, status } = body;

    if (!referenceId || !status) {
      return NextResponse.json({ success: false, error: 'Missing parameters' }, { status: 400 });
    }

    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    const pyScript = `import sys; sys.path.append('src'); from db import update_escalation_status; res = update_escalation_status('${referenceId}', '${status}'); print('OK' if res else 'FAIL')`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 5000,
    });

    const success = stdout.trim() === 'OK';
    return NextResponse.json({ success });
  } catch (err) {
    console.warn('Escalations API PATCH warning:', err);
    return NextResponse.json({ success: false, error: String(err) }, { status: 500 });
  }
}
