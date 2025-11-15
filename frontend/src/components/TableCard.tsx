import React from 'react';

interface TableCardProps {
  data: Array<Record<string, any>>;
  columns?: string[];
  title?: string;
}

const TableCard: React.FC<TableCardProps> = ({ data, columns, title }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  // If columns not provided, extract from first row
  const tableColumns = columns || Object.keys(data[0]);

  // Format column headers (convert snake_case to Title Case)
  const formatHeader = (key: string) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format cell value
  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {title && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {tableColumns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {formatHeader(column)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                {tableColumns.map((column) => (
                  <td
                    key={`${rowIndex}-${column}`}
                    className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap"
                  >
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Showing {data.length} {data.length === 1 ? 'row' : 'rows'}
        </p>
      </div>
    </div>
  );
};

export default TableCard;
