import React from 'react';

export interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => React.ReactNode;
  className?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  isLoading?: boolean;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No records found.',
  isLoading = false,
}: TableProps<T>) {
  if (isLoading) {
    return (
      <div className="py-8 text-center text-niyam-text-muted">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-niyam-primary border-t-transparent mb-2" />
        <p className="text-sm">Loading records...</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="py-12 text-center text-niyam-text-muted bg-niyam-surface rounded-lg border border-niyam-border">
        <p className="text-sm font-medium">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-niyam-border bg-niyam-surface shadow-sm">
      <table className="w-full text-left text-sm border-collapse">
        <thead>
          <tr className="bg-niyam-surface-alt border-b border-niyam-border text-niyam-text font-semibold">
            {columns.map((col, index) => (
              <th key={index} scope="col" className={`px-4 py-3 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-niyam-border">
          {data.map((item) => (
            <tr key={keyExtractor(item)} className="hover:bg-niyam-primary-tint/30 transition-colors">
              {columns.map((col, colIndex) => (
                <td key={colIndex} className={`px-4 py-3.5 text-niyam-text ${col.className || ''}`}>
                  {col.cell ? col.cell(item) : col.accessorKey ? String(item[col.accessorKey] ?? '') : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
