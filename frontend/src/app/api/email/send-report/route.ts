import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Get authorization header
    const authHeader = request.headers.get('authorization');
    
    // Forward to FastAPI backend through Traefik
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/email/send-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader || '',
        'X-Forwarded-For': request.headers.get('x-forwarded-for') || '',
        'X-Forwarded-Proto': request.headers.get('x-forwarded-proto') || 'http',
      },
      body: JSON.stringify(body),
    });

    let data;
    try {
      data = await response.json();
    } catch (e) {
      data = { detail: 'Server error. Please try again.' };
    }
    
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
