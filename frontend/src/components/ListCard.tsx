import React from 'react';

interface ListCardProps {
  items: string[] | Array<Record<string, any>>;
  title?: string;
}

const ListCard: React.FC<ListCardProps> = ({ items, title }) => {
  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-gray-500 text-center">No items available</p>
      </div>
    );
  }

  // Convert objects to strings if needed
  const listItems = items.map((item) => 
    typeof item === 'string' ? item : JSON.stringify(item)
  );

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {title && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}
      <ul className="divide-y divide-gray-200">
        {listItems.map((item, index) => (
          <li
            key={index}
            className="px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-medium mr-3">
                {index + 1}
              </span>
              <span className="text-sm text-gray-700 flex-1">{item}</span>
            </div>
          </li>
        ))}
      </ul>
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          {items.length} {items.length === 1 ? 'item' : 'items'}
        </p>
      </div>
    </div>
  );
};

export default ListCard;
