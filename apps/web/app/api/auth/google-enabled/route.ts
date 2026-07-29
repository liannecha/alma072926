import { NextResponse } from 'next/server';
import { isGoogleAuthConfigured } from '../../../../lib/auth';

export function GET() {
  return NextResponse.json({ enabled: isGoogleAuthConfigured });
}
