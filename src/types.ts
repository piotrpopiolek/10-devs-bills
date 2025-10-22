import { Database } from '../astro/src/db/database.types'

// ============================================================================
// BASE TYPES FROM DATABASE ENTITIES
// ============================================================================

// Extract base types from database entities
export type User = Database['public']['Tables']['users']['Row']
export type Bill = Database['public']['Tables']['bills']['Row']
export type BillItem = Database['public']['Tables']['bill_items']['Row']
export type Shop = Database['public']['Tables']['shops']['Row']
export type Category = Database['public']['Tables']['categories']['Row']
export type Product = Database['public']['Tables']['indexes']['Row']
export type ProductAlias = Database['public']['Tables']['index_aliases']['Row']
export type TelegramMessage = Database['public']['Tables']['telegram_messages']['Row']

// Extract enum types
export type ProcessingStatus = Database['public']['Enums']['processing_status']
export type VerificationSource = Database['public']['Enums']['verification_source']
export type TelegramMessageStatus = Database['public']['Enums']['telegram_message_status']
export type TelegramMessageType = Database['public']['Enums']['telegram_message_type']

// ============================================================================
// COMMON TYPES
// ============================================================================

/**
 * Standard pagination information for list responses
 */
export interface PaginationInfo {
  page: number
  limit: number
  total: number
  pages: number
}

/**
 * Standard error response format
 */
export interface ErrorResponse {
  error: string
  message: string
  code?: string
}

/**
 * Date range for filtering
 */
export interface DateRange {
  from?: string
  to?: string
}

// ============================================================================
// AUTHENTICATION DTOs
// ============================================================================

/**
 * Request DTO for generating magic link authentication
 * Maps to Telegram user ID and redirect URL
 */
export interface MagicLinkRequest {
  telegram_user_id: number
  redirect_url: string
}

/**
 * Response DTO for magic link generation
 * Contains the generated link and expiration information
 */
export interface MagicLinkResponse {
  magic_link: string
  expires_at: string
  sent_to_telegram: boolean
}

/**
 * Response DTO for successful authentication verification
 * Contains JWT tokens and user information
 */
export interface AuthVerifyResponse {
  access_token: string
  refresh_token: string
  user: Pick<User, 'id' | 'external_id' | 'is_active' | 'created_at'>
}

// ============================================================================
// USER DTOs
// ============================================================================

/**
 * User usage statistics for monthly limits
 */
export interface UserUsageStats {
  bills_this_month: number
  monthly_limit: number
  remaining_bills: number
}

/**
 * Complete user profile response with usage statistics
 * Extends base user entity with usage information
 */
export interface UserProfileResponse extends Pick<User, 'id' | 'external_id' | 'is_active' | 'created_at'> {
  usage: UserUsageStats
}

// ============================================================================
// SHOP DTOs
// ============================================================================

/**
 * Basic shop information response
 * Derived from shops table with additional computed fields
 */
export interface ShopResponse extends Pick<Shop, 'id' | 'name' | 'address' | 'created_at'> {
  bills_count: number
  total_spent?: number
}

/**
 * Shop summary for list views
 * Minimal shop information for paginated lists
 */
export interface ShopListItem extends Pick<Shop, 'id' | 'name' | 'address' | 'created_at'> {
  bills_count: number
}

/**
 * Paginated shop list response
 */
export interface ShopListResponse {
  shops: ShopListItem[]
  pagination: PaginationInfo
}

// ============================================================================
// CATEGORY DTOs
// ============================================================================

/**
 * Category response with hierarchical structure
 * Extends base category with children and product count
 */
export interface CategoryResponse extends Pick<Category, 'id' | 'name' | 'parent_id' | 'created_at'> {
  children: CategoryResponse[]
  products_count: number
}

/**
 * List of categories with hierarchy
 */
export interface CategoryListResponse {
  categories: CategoryResponse[]
}

// ============================================================================
// PRODUCT DTOs
// ============================================================================

/**
 * Product information with category details
 * Extends indexes table with category information and usage statistics
 */
export interface ProductResponse extends Pick<Product, 'id' | 'name' | 'synonyms' | 'created_at'> {
  category: Pick<Category, 'id' | 'name'>
  usage_count: number
}

/**
 * Product summary for list views
 * Minimal product information for paginated lists
 */
export interface ProductListItem extends Pick<Product, 'id' | 'name' | 'synonyms' | 'created_at'> {
  category: Pick<Category, 'id' | 'name'>
  usage_count: number
}

/**
 * Paginated product list response
 */
export interface ProductListResponse {
  products: ProductListItem[]
  pagination: PaginationInfo
}

// ============================================================================
// BILL DTOs
// ============================================================================

/**
 * Request DTO for bill upload
 * Multipart form data for image upload with metadata
 */
export interface BillUploadRequest {
  image: File
  bill_date: string
  shop_name: string
  shop_address?: string
}

/**
 * Basic bill response for creation and list views
 * Derived from bills table with shop information
 */
export interface BillResponse extends Pick<Bill, 'id' | 'status' | 'bill_date' | 'total_amount' | 'created_at'> {
  shop: Pick<Shop, 'id' | 'name' | 'address'>
  items: BillItemDetailResponse[]
}

/**
 * Bill summary for list views
 * Minimal bill information for paginated lists
 */
export interface BillListItem extends Pick<Bill, 'id' | 'bill_date' | 'total_amount' | 'status' | 'created_at'> {
  shop: Pick<Shop, 'id' | 'name'>
  items_count: number
}

/**
 * Paginated bill list response
 */
export interface BillListResponse {
  bills: BillListItem[]
  pagination: PaginationInfo
}

/**
 * Detailed bill response with complete information
 * Extends basic bill response with image details and full item information
 */
export interface BillDetailResponse extends BillResponse {
  image_url: string | null
  image_expires_at: string | null
  updated_at: string
}

// ============================================================================
// BILL ITEM DTOs
// ============================================================================

/**
 * Request DTO for bill item verification
 * Allows users to verify or correct bill item information
 */
export interface BillItemVerificationRequest {
  is_verified: boolean
  quantity: number
  unit_price: number
  total_price: number
  product_id: number
  notes?: string
}

/**
 * Detailed bill item response with product information
 * Extends bill_items table with product and category details
 */
export interface BillItemDetailResponse extends Pick<BillItem, 'id' | 'quantity' | 'unit_price' | 'total_price' | 'original_text' | 'confidence_score' | 'is_verified' | 'verification_source'> {
  product: ProductResponse
}

/**
 * Response DTO after bill item verification
 * Updated item information with verification source
 */
export interface BillItemVerificationResponse extends Pick<BillItem, 'id' | 'quantity' | 'unit_price' | 'total_price' | 'is_verified' | 'verification_source'> {
  product: ProductResponse
  updated_at: string
}

/**
 * Bill item pending verification with context
 * Includes bill and suggested product information
 */
export interface PendingVerificationItem extends Pick<BillItem, 'id' | 'quantity' | 'unit_price' | 'total_price' | 'original_text' | 'confidence_score'> {
  bill: {
    id: number
    bill_date: string
    shop: Pick<Shop, 'name'>
  }
  suggested_product: ProductResponse
}

/**
 * Response for items pending verification
 * Paginated list of items requiring user verification
 */
export interface PendingVerificationResponse {
  items: PendingVerificationItem[]
  pagination: PaginationInfo
}

// ============================================================================
// REPORT DTOs
// ============================================================================

/**
 * Category expense breakdown for reports
 * Shows spending by category with percentage
 */
export interface CategoryExpense {
  category: Pick<Category, 'id' | 'name'>
  amount: number
  percentage: number
}

/**
 * Shop expense breakdown for reports
 * Shows spending by shop with bill count
 */
export interface ShopExpense {
  shop: Pick<Shop, 'id' | 'name'>
  amount: number
  bills_count: number
}

/**
 * Daily breakdown for weekly reports
 * Shows daily spending within a week
 */
export interface DailyBreakdown {
  date: string
  amount: number
  bills_count: number
}

/**
 * Weekly breakdown for monthly reports
 * Shows weekly spending within a month
 */
export interface WeeklyBreakdown {
  week_start: string
  amount: number
}

/**
 * Daily expense report response
 * Shows spending for a specific day
 */
export interface DailyReportResponse {
  date: string
  total_amount: number
  bills_count: number
  top_categories: CategoryExpense[]
  shops: ShopExpense[]
}

/**
 * Weekly expense report response
 * Shows spending for a specific week
 */
export interface WeeklyReportResponse {
  week_start: string
  week_end: string
  total_amount: number
  bills_count: number
  daily_breakdown: DailyBreakdown[]
  top_categories: CategoryExpense[]
}

/**
 * Monthly expense report response
 * Shows spending for a specific month
 */
export interface MonthlyReportResponse {
  month: string
  total_amount: number
  bills_count: number
  daily_average: number
  top_categories: CategoryExpense[]
  top_shops: ShopExpense[]
  weekly_breakdown: WeeklyBreakdown[]
}

// ============================================================================
// COMMAND MODELS
// ============================================================================

/**
 * Command model for creating a new bill
 * Maps upload request to database insert operation
 */
export interface CreateBillCommand {
  user_id: number
  bill_date: string
  shop_name: string
  shop_address?: string
  image_file: File
}

/**
 * Command model for updating bill item verification
 * Maps verification request to database update operation
 */
export interface VerifyBillItemCommand {
  item_id: number
  user_id: number
  is_verified: boolean
  quantity: number
  unit_price: number
  total_price: number
  product_id: number
  notes?: string
}

/**
 * Command model for processing bill image
 * Internal command for OCR and AI processing pipeline
 */
export interface ProcessBillImageCommand {
  bill_id: number
  image_url: string
  user_id: number
}

/**
 * Command model for sending Telegram notification
 * Maps to telegram_messages table insert
 */
export interface SendTelegramNotificationCommand {
  user_id: number
  chat_id: number
  content: string
  message_type: TelegramMessageType
  bill_id?: number
  file_id?: string
  file_path?: string
}

// ============================================================================
// QUERY MODELS
// ============================================================================

/**
 * Query model for filtering bills
 * Maps query parameters to database filters
 */
export interface BillQuery {
  user_id: number
  page?: number
  limit?: number
  status?: ProcessingStatus
  shop_id?: number
  date_from?: string
  date_to?: string
}

/**
 * Query model for filtering products
 * Maps query parameters to database filters
 */
export interface ProductQuery {
  search?: string
  category_id?: number
  page?: number
  limit?: number
}

/**
 * Query model for filtering shops
 * Maps query parameters to database filters
 */
export interface ShopQuery {
  search?: string
  page?: number
  limit?: number
}

/**
 * Query model for category listing
 * Maps query parameters to database filters
 */
export interface CategoryQuery {
  parent_id?: number
  include_children?: boolean
}

/**
 * Query model for pending verification items
 * Maps query parameters to database filters
 */
export interface PendingVerificationQuery {
  user_id: number
  page?: number
  limit?: number
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Utility type for creating response DTOs with optional fields
 */
export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * Utility type for creating request DTOs with required fields
 */
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

/**
 * Utility type for API responses with consistent structure
 */
export type ApiResponse<T> = {
  data: T
  success: boolean
  message?: string
}

/**
 * Utility type for paginated API responses
 */
export type PaginatedResponse<T> = {
  data: T[]
  pagination: PaginationInfo
  success: boolean
}
