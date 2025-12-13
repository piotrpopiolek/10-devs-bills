/**
 * Formatuje kwotę jako walutę
 * @param amount - Kwota do sformatowania
 * @param currency - Kod waluty (domyślnie "PLN")
 * @returns Sformatowana kwota (np. "124.50 PLN")
 */
export function formatCurrency(
  amount: number | null | undefined,
  currency: string = 'PLN'
): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return `0.00 ${currency}`;
  }

  // Formatuj z 2 miejscami po przecinku
  const formatted = amount.toFixed(2);
  return `${formatted} ${currency}`;
}

/**
 * Formatuje datę do wyświetlenia
 * @param date - Data jako string ISO 8601 lub obiekt Date
 * @returns Sformatowana data (np. "15.01.2024")
 */
export function formatDate(date: string | Date): string {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    if (isNaN(dateObj.getTime())) {
      // Jeśli data jest nieprawidłowa, zwróć pusty string lub fallback
      return '';
    }

    // Formatuj jako DD.MM.YYYY
    const day = dateObj.getDate().toString().padStart(2, '0');
    const month = (dateObj.getMonth() + 1).toString().padStart(2, '0');
    const year = dateObj.getFullYear();

    return `${day}.${month}.${year}`;
  } catch (error) {
    console.error('Error formatting date:', error);
    return '';
  }
}

/**
 * Oblicza trend (procentową zmianę) między dwiema wartościami
 * @param current - Bieżąca wartość
 * @param previous - Poprzednia wartość
 * @returns Dane trendu lub null jeśli nie można obliczyć (np. dzielenie przez zero)
 */
export function calculateTrend(
  current: number,
  previous: number
): { value: number; isPositive: boolean } | null {
  // Jeśli poprzednia wartość to 0, nie można obliczyć trendu
  if (previous === 0) {
    return null;
  }

  // Oblicz procentową zmianę
  const change = ((current - previous) / previous) * 100;
  const isPositive = change >= 0;

  return {
    value: Math.abs(change),
    isPositive,
  };
}

/**
 * Oblicza poprzedni miesiąc w formacie YYYY-MM
 * @param currentMonth - Bieżący miesiąc w formacie YYYY-MM (opcjonalnie)
 * @returns Poprzedni miesiąc w formacie YYYY-MM
 */
export function getPreviousMonth(currentMonth?: string): string {
  const now = currentMonth ? new Date(`${currentMonth}-01`) : new Date();
  const previousMonth = new Date(now);
  previousMonth.setMonth(previousMonth.getMonth() - 1);

  const year = previousMonth.getFullYear();
  const month = (previousMonth.getMonth() + 1).toString().padStart(2, '0');

  return `${year}-${month}`;
}

/**
 * Pobiera bieżący miesiąc w formacie YYYY-MM
 * @returns Bieżący miesiąc w formacie YYYY-MM
 */
export function getCurrentMonth(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = (now.getMonth() + 1).toString().padStart(2, '0');

  return `${year}-${month}`;
}
