import type { Database, Tables, TablesInsert, TablesUpdate, Enums } from './db/database.types'

// ============================================================================
// BASE TYPES FROM DATABASE
// ============================================================================

export type User = Tables<'users'>
export type Bill = Tables<'bills'>
export type BillItem = Tables<'bill_items'>
export type Shop = Tables<'shops'>
export type Category = Tables<'categories'>
export type Product = Tables<'indexes'>
export type ProductAlias = Tables<'index_aliases'>
export type TelegramMessage = Tables<'telegram_messages'>

// Database enums
export type ProcessingStatus = Enums<'processing_status'>
export type VerificationSource = Enums<'verification_source'>
export type TelegramMessageType = Enums<'telegram_message_type'>
export type TelegramMessageStatus = Enums<'telegram_message_status'>

// ============================================================================
// COMMON UTILITY TYPES
// ============================================================================

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  pages: number
}

export interface PaginatedResponse<T> {
  pagination: PaginationMeta
}

// ============================================================================
// AUTHENTICATION DTOs
// ============================================================================

export interface MagicLinkRequest {
  telegram_user_id: number
  redirect_url: string
}

export interface MagicLinkResponse {
  magic_link: string
  expires_at: string
  sent_to_telegram: boolean
}

export interface AuthVerifyResponse {
  access_token: string
  refresh_token: string
  user: UserProfile
}

// ============================================================================
// USER DTOs
// ============================================================================

export interface UsageStats {
  bills_this_month: number
  monthly_limit: number
  remaining_bills: number
}

export interface UserProfile extends Pick<User, 'id' | 'external_id' | 'is_active' | 'created_at'> {
  usage: UsageStats
}

// ============================================================================
// SHOP DTOs
// ============================================================================

export interface ShopResponse extends Pick<Shop, 'id' | 'name' | 'address' | 'created_at'> {
  bills_count: number
}

export interface ShopDetailResponse extends ShopResponse {
  total_spent: number
}

export interface ShopListResponse extends PaginatedResponse<ShopResponse[]> {
  shops: ShopResponse[]
}

// ============================================================================
// CATEGORY DTOs
// ============================================================================

export interface CategoryResponse extends Pick<Category, 'id' | 'name' | 'parent_id' | 'created_at'> {
  children: CategoryResponse[]
  products_count: number
}

export interface CategoryListResponse {
  categories: CategoryResponse[]
}

// ============================================================================
// PRODUCT DTOs
// ============================================================================

export interface ProductResponse extends Pick<Product, 'id' | 'name' | 'synonyms' | 'created_at'> {
  category: Pick<Category, 'id' | 'name'>
  usage_count: number
}

export interface ProductListResponse extends PaginatedResponse<ProductResponse[]> {
  products: ProductResponse[]
}

// ============================================================================
// BILL ITEM DTOs
// ============================================================================

export interface BillItemVerifyRequest {
  is_verified: boolean
  quantity?: number
  unit_price?: number
  total_price?: number
  product_id?: number
  notes?: string
}

export interface BillItemResponse extends Pick<BillItem, 'id' | 'quantity' | 'unit_price' | 'total_price' | 'original_text' | 'confidence_score' | 'is_verified' | 'verification_source'> {
  product: ProductResponse | null
}

export interface BillItemVerifyResponse extends BillItemResponse {
  updated_at: string
}

export interface PendingVerificationItem extends Pick<BillItem, 'id' | 'quantity' | 'unit_price' | 'total_price' | 'original_text' | 'confidence_score'> {
  bill: {
    id: number
    bill_date: string
    shop: Pick<Shop, 'name'>
  }
  suggested_product: ProductResponse | null
}

export interface PendingVerificationResponse extends PaginatedResponse<PendingVerificationItem[]> {
  items: PendingVerificationItem[]
}

// ============================================================================
// BILL DTOs
// ============================================================================

export interface BillCreateRequest {
  image: File
  bill_date: string
  shop_name?: string
  shop_address?: string
}

export interface BillResponse extends Pick<Bill, 'id' | 'bill_date' | 'total_amount' | 'status' | 'created_at'> {
  shop: ShopResponse | null
  items_count: number
}

export interface BillDetailResponse extends Pick<Bill, 'id' | 'bill_date' | 'total_amount' | 'status' | 'image_url' | 'image_expires_at' | 'created_at' | 'updated_at'> {
  shop: ShopResponse | null
  items: BillItemResponse[]
}

export interface BillListResponse extends PaginatedResponse<BillResponse[]> {
  bills: BillResponse[]
}

// ============================================================================
// REPORT DTOs
// ============================================================================

export interface CategorySummary {
  category: Pick<Category, 'id' | 'name'>
  amount: number
  percentage: number
}

export interface ShopSummary {
  shop: Pick<Shop, 'id' | 'name'>
  amount: number
  bills_count: number
}

export interface DailyBreakdown {
  date: string
  amount: number
  bills_count: number
}

export interface WeeklyBreakdown {
  week_start: string
  amount: number
}

export interface DailyReportResponse {
  date: string
  total_amount: number
  bills_count: number
  top_categories: CategorySummary[]
  shops: ShopSummary[]
}

export interface WeeklyReportResponse {
  week_start: string
  week_end: string
  total_amount: number
  bills_count: number
  daily_breakdown: DailyBreakdown[]
  top_categories: CategorySummary[]
}

export interface MonthlyReportResponse {
  month: string
  total_amount: number
  bills_count: number
  daily_average: number
  top_categories: CategorySummary[]
  top_shops: ShopSummary[]
  weekly_breakdown: WeeklyBreakdown[]
}

// ============================================================================
// TELEGRAM DTOs
// ============================================================================

export interface TelegramWebhookPayload {
  update_id: number
  message?: {
    message_id: number
    from: {
      id: number
      is_bot: boolean
      first_name: string
      last_name?: string
      username?: string
    }
    chat: {
      id: number
      type: string
    }
    date: number
    text?: string
    photo?: Array<{
      file_id: string
      file_unique_id: string
      width: number
      height: number
      file_size?: number
    }>
    document?: {
      file_name: string
      mime_type: string
      file_id: string
      file_unique_id: string
      file_size?: number
    }
  }
}

// ============================================================================
// COMMAND MODELS (for mutations)
// ============================================================================

export interface CreateBillCommand {
  bill_date: string
  shop_name?: string
  shop_address?: string
  image_file: File
}

export interface UpdateBillItemCommand {
  is_verified: boolean
  quantity?: number
  unit_price?: number
  total_price?: number
  product_id?: number
  notes?: string
}

export interface CreateShopCommand {
  name: string
  address?: string
}

export interface UpdateShopCommand {
  name?: string
  address?: string
}

export interface CreateCategoryCommand {
  name: string
  parent_id?: number
}

export interface UpdateCategoryCommand {
  name?: string
  parent_id?: number
}

export interface CreateProductCommand {
  name: string
  synonyms?: string[]
  category_id?: number
}

export interface UpdateProductCommand {
  name?: string
  synonyms?: string[]
  category_id?: number
}

// ============================================================================
// API RESPONSE WRAPPERS
// ============================================================================

export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

export interface ApiError {
  error: string
  message: string
  status_code: number
}

// ============================================================================
// QUERY PARAMETERS
// ============================================================================

export interface BillsQueryParams {
  page?: number
  limit?: number
  status?: ProcessingStatus
  shop_id?: number
  date_from?: string
  date_to?: string
}

export interface ShopsQueryParams {
  search?: string
  page?: number
  limit?: number
}

export interface CategoriesQueryParams {
  parent_id?: number
  include_children?: boolean
}

export interface ProductsQueryParams {
  search?: string
  category_id?: number
  page?: number
  limit?: number
}

export interface PendingVerificationQueryParams {
  page?: number
  limit?: number
}

export interface ReportsQueryParams {
  date?: string
  week_start?: string
  month?: string
}
