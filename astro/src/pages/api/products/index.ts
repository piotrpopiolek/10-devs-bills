import type { APIRoute } from 'astro';
import { z } from 'zod';
import type { ProductListResponse, ApiResponse } from '@/types';

// Mark this route as dynamic (not prerendered)
export const prerender = false;

// Zod schema for query parameters validation
const ProductsQuerySchema = z.object({
  search: z.string().optional().default(''),
  category_id: z.coerce.number().int().positive().optional(),
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const GET: APIRoute = async ({ request }) => {
  const url = new URL(request.url);
  
  // Parse and validate query parameters using Zod
  const parseResult = ProductsQuerySchema.safeParse({
    search: url.searchParams.get('search') || '',
    category_id: url.searchParams.get('category_id') || undefined,
    skip: url.searchParams.get('skip') || '0',
    limit: url.searchParams.get('limit') || '20',
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

  const { search, category_id, skip, limit } = parseResult.data;
  
  const queryParams = new URLSearchParams();
  queryParams.append('skip', skip.toString());
  queryParams.append('limit', limit.toString());
  if (search) {
    queryParams.append('search', search);
  }
  if (category_id !== undefined) {
    queryParams.append('category_id', category_id.toString());
  }

  // Use environment variable for backend URL
  const BACKEND_URL = import.meta.env.BACKEND_URL;
  const API_URL = `${BACKEND_URL}/product-indexes`;

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

    const data = await response.json() as ProductListResponse;
    
    // Return wrapped response
    const apiResponse: ApiResponse<ProductListResponse> = {
      success: true,
      data: data
    };

    return new Response(JSON.stringify(apiResponse), {
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

