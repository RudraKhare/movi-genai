import React from 'react';

interface HelpCardProps {
  data: {
    title: string;
    steps: string[];
    notes?: string[];
  };
}

const HelpCard: React.FC<HelpCardProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-blue-200 overflow-hidden">
      <div className="px-4 py-3 bg-blue-50 border-b border-blue-200 flex items-center">
        <span className="text-2xl mr-2">💡</span>
        <h3 className="text-sm font-semibold text-blue-900">{data.title}</h3>
      </div>
      
      <div className="p-4">
        <ol className="space-y-3">
          {data.steps.map((step, index) => (
            <li key={index} className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-bold mr-3 mt-0.5">
                {index + 1}
              </span>
              <span className="text-sm text-gray-700 flex-1">{step}</span>
            </li>
          ))}
        </ol>

        {data.notes && data.notes.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Additional Notes
            </p>
            <ul className="space-y-1">
              {data.notes.map((note, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default HelpCard;
