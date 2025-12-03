import type { APIRoute } from 'astro';
import { z } from 'zod';

// Mark this route as dynamic (not prerendered)
export const prerender = false;

// Zod schema for query parameters validation
const ShopsQuerySchema = z.object({
  search: z.string().optional().default(''),
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(10),
});

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  
  // Parse and validate query parameters using Zod
  const parseResult = ShopsQuerySchema.safeParse({
    search: url.searchParams.get('search') || '',
    skip: url.searchParams.get('skip') || '0',
    limit: url.searchParams.get('limit') || '10',
  });

  // Early return for validation errors
  if (!parseResult.success) {
    return new Response(
      JSON.stringify({
        success: false,
        message: 'Invalid query parameters',
        errors: parseResult.error.errors,
      }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  const { search, skip, limit } = parseResult.data;
  
  const queryParams = new URLSearchParams();
  queryParams.append('skip', skip.toString());
  queryParams.append('limit', limit.toString());
  if (search) {
    queryParams.append('search', search);
  }

  // Use environment variable for backend URL
  const BACKEND_URL = import.meta.env.BACKEND_URL;
  const API_URL = `${BACKEND_URL}/shops`;

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

    const rawData: unknown = await response.json();
    console.log('Upstream API response:', JSON.stringify(rawData, null, 2));
    
    // Normalize response to match ShopListResponse interface
    // Expected: { shops: [], pagination: {} }
    // If backend returns { items: [], ... } map it to shops
    
    let normalizedData = rawData;

    if (rawData && typeof rawData === 'object' && !Array.isArray(rawData)) {
        const dataObj = rawData as Record<string, unknown>;
        if (Array.isArray(dataObj.items) && !dataObj.shops) {
            normalizedData = {
                ...dataObj,
                shops: dataObj.items
            };
        }
    } else if (Array.isArray(rawData)) {
        // If backend returns just an array
        const calculatedPage = Math.floor(skip / limit) + 1;
        normalizedData = {
            shops: rawData,
            pagination: {
                page: calculatedPage,
                limit,
                total: rawData.length,
                pages: 1
            }
        };
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
