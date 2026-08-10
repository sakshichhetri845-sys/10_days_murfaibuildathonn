import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const cookieStore = await cookies();
    const cookieUserId = cookieStore.get('bolbuddy_user_id')?.value;
    const userId = searchParams.get('userId') || cookieUserId;

    if (!userId) {
      return NextResponse.json({ success: false, memory: null }, { status: 200 });
    }

    // Resolve path to backend directory
    const repoRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(repoRoot, 'backend');

    // Execute python get_user command safely
    const pyScript = `import sys, json; sys.path.append('src'); from db import get_user; u = get_user('${userId}'); print(json.dumps(u) if u else 'null')`;

    const { stdout } = await execAsync(`uv run python -c "${pyScript}"`, {
      cwd: backendDir,
      timeout: 4000,
    });

    const userRecord = JSON.parse(stdout.trim() || 'null');

    if (!userRecord) {
      return NextResponse.json({ success: true, memory: null });
    }

    const facts = userRecord.facts || {};
    const name = userRecord.name || null;
    const learningGoal = facts.learning_goal || null;
    const topicsPracticed = facts.topics_practiced || [];
    const currentLevel = facts.current_level || null;

    return NextResponse.json({
      success: true,
      memory: {
        userId: userRecord.user_id,
        name,
        learningGoal,
        topicsPracticed,
        lastPracticedTopic:
          topicsPracticed.length > 0 ? topicsPracticed[topicsPracticed.length - 1] : null,
        currentLevel,
      },
    });
  } catch (err) {
    console.warn('Memory API fetch warning:', err);
    return NextResponse.json({ success: false, memory: null }, { status: 200 });
  }
}
