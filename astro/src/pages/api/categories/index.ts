// GET /categories endpoint - draft implementation for listing product categories
import type { NextApiRequest, NextApiResponse } from 'next'
import type { ApiError } from '../../../types'
import axios from 'axios'

// Ustaw backend URL FastAPI (pobierz z ENV lub wpisz na sztywno do testów)
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/categories'

interface GetCategoriesQuery {
  parent_id?: string
  include_children?: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET'])
    return res.status(405).json({
      error: 'method_not_allowed',
      message: 'Method Not Allowed',
      status_code: 405,
    })
  }

  // 1. Wyciągnij i waliduj parametry
  const { parent_id, include_children } = req.query as GetCategoriesQuery
  let params: Record<string, any> = {}
   
  if (parent_id !== undefined) {
    if (!/^\d+$/.test(parent_id)) {
      return res.status(400).json({
        error: 'invalid_parent_id',
        message: 'parent_id must be a positive integer',
        status_code: 400,
      } as ApiError)
    }
    params.parent_id = parseInt(parent_id, 10)
  }
  if (include_children !== undefined) {
    if (
      include_children !== 'true' &&
      include_children !== 'false' &&
      include_children !== '1' &&
      include_children !== '0'
    ) {
      return res.status(400).json({
        error: 'invalid_include_children',
        message: 'include_children must be a boolean',
        status_code: 400,
      } as ApiError)
    }
    params.include_children = ['1', 'true'].includes(include_children)
  }
  
  // 2. Forwarduj żądanie do FastAPI
  try {
    const fastapiRes = await axios.get(FASTAPI_URL, { params })
    res.status(fastapiRes.status).json(fastapiRes.data)
  } catch (err: any) {
    // Forward any FastAPI HTTP errors or generic error if unreachable
    if (err.response) {
      res.status(err.response.status).json(err.response.data)
    } else {
      res.status(500).json({
        error: 'fastapi_unreachable',
        message: 'Could not connect to backend API',
        status_code: 500,
      })
    }
  }
}
