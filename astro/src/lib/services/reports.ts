import type {
  DailyReportResponse,
  WeeklyReportResponse,
  MonthlyReportResponse,
  ApiResponse,
} from '../../types';
import { apiFetch } from '../api-client';

/**
 * Pobiera raport wydatków dziennych dla określonej daty (domyślnie dzisiaj)
 * @param date - Data w formacie ISO 8601 (YYYY-MM-DD), domyślnie dzisiaj
 * @returns Raport dzienny z wydatkami
 */
export const getDailyReport = async (
  date?: string
): Promise<DailyReportResponse> => {
  const queryParams = new URLSearchParams();

  if (date) {
    queryParams.append('date', date);
  }

  try {
    const url = `/api/reports/daily${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiFetch(url);

    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Nieprawidłowy format daty');
      }
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<DailyReportResponse> | DailyReportResponse =
      await response.json();

    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch daily report');
      }
      return data.data;
    }

    return data as DailyReportResponse;
  } catch (error) {
    console.error('Error fetching daily report:', error);
    throw error;
  }
};

/**
 * Pobiera raport wydatków tygodniowych dla określonego tygodnia
 * @param weekStart - Data rozpoczęcia tygodnia (poniedziałek) w formacie ISO 8601 (YYYY-MM-DD)
 * @returns Raport tygodniowy z wydatkami
 */
export const getWeeklyReport = async (
  weekStart?: string
): Promise<WeeklyReportResponse> => {
  const queryParams = new URLSearchParams();

  if (weekStart) {
    queryParams.append('week_start', weekStart);
  }

  try {
    const url = `/api/reports/weekly${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiFetch(url);

    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Nieprawidłowy format daty');
      }
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<WeeklyReportResponse> | WeeklyReportResponse =
      await response.json();

    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch weekly report');
      }
      return data.data;
    }

    return data as WeeklyReportResponse;
  } catch (error) {
    console.error('Error fetching weekly report:', error);
    throw error;
  }
};

/**
 * Pobiera raport wydatków miesięcznych dla określonego miesiąca
 * @param month - Miesiąc w formacie YYYY-MM, domyślnie bieżący miesiąc
 * @returns Raport miesięczny z wydatkami
 */
export const getMonthlyReport = async (
  month?: string
): Promise<MonthlyReportResponse> => {
  const queryParams = new URLSearchParams();

  if (month) {
    queryParams.append('month', month);
  }

  try {
    const url = `/api/reports/monthly${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiFetch(url);

    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Nieprawidłowy format miesiąca');
      }
      if (response.status === 401) {
        throw new Error('Brak autoryzacji');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<MonthlyReportResponse> | MonthlyReportResponse =
      await response.json();

    // Handle both wrapped ApiResponse and direct response for flexibility
    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch monthly report');
      }
      const report = data.data;
      console.log('Unwrapped monthly report:', {
        month: report.month,
        total_amount: report.total_amount,
        top_categories_count: report.top_categories?.length || 0,
        top_shops_count: report.top_shops?.length || 0,
        weekly_breakdown_count: report.weekly_breakdown?.length || 0,
      });
      return report;
    }

    console.log('Direct monthly report response (not wrapped):', {
      month: (data as MonthlyReportResponse).month,
      total_amount: (data as MonthlyReportResponse).total_amount,
    });
    return data as MonthlyReportResponse;
  } catch (error) {
    console.error('Error fetching monthly report:', error);
    throw error;
  }
};
