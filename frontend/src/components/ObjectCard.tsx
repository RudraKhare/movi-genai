import React from 'react';

interface ObjectCardProps {
  data: Record<string, any>;
  title?: string;
}

const ObjectCard: React.FC<ObjectCardProps> = ({ data, title }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  // Format key (convert snake_case to Title Case)
  const formatKey = (key: string) => {
    return key
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Format value with type-specific rendering
  const formatValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400 italic">null</span>;
    }
    if (typeof value === 'boolean') {
      return (
        <span className={value ? 'text-green-600' : 'text-red-600'}>
          {value ? '✓ True' : '✗ False'}
        </span>
      );
    }
    if (typeof value === 'number') {
      return <span className="text-blue-600 font-mono">{value}</span>;
    }
    if (Array.isArray(value)) {
      return (
        <div className="mt-1 space-y-1">
          {value.map((item, idx) => (
            <div key={idx} className="text-sm text-gray-600 pl-4 border-l-2 border-gray-200">
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
            </div>
          ))}
        </div>
      );
    }
    if (typeof value === 'object') {
      return (
        <pre className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }
    return <span className="text-gray-700">{String(value)}</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {title && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}
      <dl className="divide-y divide-gray-200">
        {Object.entries(data).map(([key, value]) => (
          <div
            key={key}
            className="px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <dt className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
              {formatKey(key)}
            </dt>
            <dd className="text-sm">
              {formatValue(value)}
            </dd>
          </div>
        ))}
      </dl>
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          {Object.keys(data).length} {Object.keys(data).length === 1 ? 'field' : 'fields'}
        </p>
      </div>
    </div>
  );
};

export default ObjectCard;
