import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  const search = url.searchParams.get('search') || '';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '10');
  
  const queryParams = new URLSearchParams();
  queryParams.append('page', page.toString());
  queryParams.append('limit', limit.toString());
  if (search) {
    queryParams.append('search', search);
  }

  // TODO: Move this to env var
  const API_URL = 'http://127.0.0.1:8000/api/v1/shops';

  console.log(`Proxying request to: ${API_URL}/?${queryParams.toString()}`);

  try {
    const response = await fetch(`${API_URL}/?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error(`Upstream API error: ${response.status} ${errorText}`);
        return new Response(JSON.stringify({
            success: false,
            message: `Upstream API error: ${response.status}`
        }), { status: response.status });
    }

    const rawData = await response.json();
    console.log('Upstream API response:', JSON.stringify(rawData, null, 2));
    
    // Normalize response to match ShopListResponse interface
    // Expected: { shops: [], pagination: {} }
    // If backend returns { items: [], ... } map it to shops
    
    let normalizedData = rawData;

    if (rawData && typeof rawData === 'object') {
        if (Array.isArray(rawData.items) && !rawData.shops) {
            normalizedData = {
                ...rawData,
                shops: rawData.items
            };
        } else if (Array.isArray(rawData) && !rawData.shops) {
             // If backend returns just an array
             normalizedData = {
                 shops: rawData,
                 pagination: {
                     page,
                     limit,
                     total: rawData.length,
                     pages: 1
                 }
             };
        }
    }

    return new Response(JSON.stringify({
      success: true,
      data: normalizedData
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      }
    });

  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(JSON.stringify({
      success: false,
      message: error instanceof Error ? error.message : 'Unknown proxy error'
    }), { status: 500 });
  }
};
