/**
 * Shared file-download and export utilities.
 *
 * These helpers centralise the blob-download pattern that was previously
 * duplicated across DashboardPage (CSV export) and CommandsPage (JSON export).
 */

/**
 * Trigger a browser file download for arbitrary string data.
 */
export function downloadFile(data: string, filename: string, mimeType: string): void {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/**
 * Export a JavaScript value as a pretty-printed JSON file download.
 */
export function exportAsJSON(data: unknown, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  downloadFile(json, filename, 'application/json');
}

/**
 * Export tabular data as a CSV file download.
 *
 * @param headers - Column header names
 * @param rows    - Array of row arrays (each inner array is one row of cells)
 * @param filename - Download filename
 */
export function exportAsCSV(headers: string[], rows: string[][], filename: string): void {
  const escapeCsvCell = (cell: string): string => {
    if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
      return `"${cell.replace(/"/g, '""')}"`;
    }
    return cell;
  };

  const headerLine = headers.map(escapeCsvCell).join(',');
  const bodyLines = rows.map(row => row.map(escapeCsvCell).join(','));
  const csv = [headerLine, ...bodyLines].join('\n');

  downloadFile(csv, filename, 'text/csv;charset=utf-8');
}
