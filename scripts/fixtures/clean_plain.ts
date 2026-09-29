export function formatCents(cents: number): string {
  const yuan = cents / 100
  return yuan.toFixed(2)
}

export function clamp(low: number, high: number, v: number): number {
  if (v < low) {
    return low
  }
  return v > high ? high : v
}
