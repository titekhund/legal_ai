import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('query') || '';
    const documentType = searchParams.get('document_type') || '';
    const language = searchParams.get('language') || 'ka';
    const limit = searchParams.get('limit') || '10';

    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (documentType) params.append('document_type', documentType);
    params.append('language', language);
    params.append('limit', limit);

    const response = await fetch(
      `${API_BASE_URL}/v1/documents/templates?${params.toString()}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { error: error.detail || 'Failed to fetch templates' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching templates:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
