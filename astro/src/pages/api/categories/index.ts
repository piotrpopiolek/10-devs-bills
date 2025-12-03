import type { APIRoute } from 'astro';
import { z } from 'zod';

// Mark this route as dynamic (not prerendered)
export const prerender = false;

// Zod schema for query parameters validation
const CategoriesQuerySchema = z.object({
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(100),
});

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  
  // Parse and validate query parameters using Zod
  const parseResult = CategoriesQuerySchema.safeParse({
    skip: url.searchParams.get('skip') || '0',
    limit: url.searchParams.get('limit') || '100',
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

  const { skip, limit } = parseResult.data;
  
  const queryParams = new URLSearchParams();
  queryParams.append('skip', skip.toString());
  queryParams.append('limit', limit.toString());

  // Use environment variable for backend URL
  const BACKEND_URL = import.meta.env.BACKEND_URL;
  const API_URL = `${BACKEND_URL}/categories`;

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
    
    // Normalize response to match CategoryListResponse interface
    // Backend returns PaginatedResponse[CategoryResponse] with: items, total, skip, limit
    // We need: categories, pagination: { page, limit, total, pages }
    
    let normalizedData = rawData;

    if (rawData && typeof rawData === 'object' && !Array.isArray(rawData)) {
        const dataObj = rawData as Record<string, unknown>;
        
        // Backend returns items array, normalize to categories
        const categories = Array.isArray(dataObj.items) ? dataObj.items : (Array.isArray(dataObj.categories) ? dataObj.categories : []);
        
        // Extract pagination info from backend response
        const backendTotal = typeof dataObj.total === 'number' ? dataObj.total : categories.length;
        const backendSkip = typeof dataObj.skip === 'number' ? dataObj.skip : skip;
        const backendLimit = typeof dataObj.limit === 'number' ? dataObj.limit : limit;
        
        // Calculate page and pages for UI
        const calculatedPage = Math.floor(backendSkip / backendLimit) + 1;
        const calculatedPages = Math.ceil(backendTotal / backendLimit);
        
        normalizedData = {
            categories,
            pagination: {
                page: calculatedPage,
                limit: backendLimit,
                total: backendTotal,
                pages: calculatedPages
            }
        };
    } else if (Array.isArray(rawData)) {
        // If backend returns just an array
        const calculatedPage = Math.floor(skip / limit) + 1;
        normalizedData = {
            categories: rawData,
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
