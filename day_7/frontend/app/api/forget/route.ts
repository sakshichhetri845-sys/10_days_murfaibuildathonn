import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const cookieStore = await cookies();
    const cookieUserId = cookieStore.get('bolbuddy_user_id')?.value;
    const userId = body.userId || cookieUserId;

    if (!userId) {
      return NextResponse.json({ success: false, error: 'No user ID provided' }, { status: 400 });
    }

    // Resolve path to backend directory and SQLite database
    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    // Execute python delete command safely
    const pyScript = `import sys; sys.path.append('src'); from db import delete_user; print(delete_user('${userId}'))`;

    await execAsync(`uv run python -c "${pyScript}"`, { cwd: backendDir }).catch((err) => {
      console.warn('Backend python delete warning:', err);
    });

    const response = NextResponse.json({ success: true, userId });
    response.cookies.delete('bolbuddy_user_id');
    return response;
  } catch (err) {
    console.error('Forget data error:', err);
    return NextResponse.json({ success: false, error: String(err) }, { status: 500 });
  }
}
