import { useState, useEffect } from 'react';
import Badge from './ui/Badge';

export default function ReportTable({ reports, selectedReport, onSelect }) {
  // Real Pagination State!
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 7;

  // If the search query changes the amount of reports, snap back to page 1
  useEffect(() => {
    setCurrentPage(1);
  }, [reports]);

  const totalPages = Math.max(1, Math.ceil(reports.length / itemsPerPage));
  const currentData = reports.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const getRiskColor = (risk) => {
    if (risk === 'Invalid') return 'text-gray-600 bg-gray-100';
    if (risk?.includes('High')) return 'text-red-700 bg-red-100';
    if (risk?.includes('Elevated') || risk?.includes('MCI')) return 'text-orange-700 bg-orange-100';
    return 'text-green-700 bg-green-100';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-gray-50/80 border-b border-gray-200 text-gray-500 font-medium">
            <tr>
              <th className="px-6 py-4">PATIENT NAME</th>
              <th className="px-6 py-4">DATE</th>
              <th className="px-6 py-4">RESULT</th>
              <th className="px-6 py-4">CONFIDENCE</th>
              <th className="px-6 py-4 text-center">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {currentData.length > 0 ? currentData.map((row) => (
              <tr
                key={row.id}
                onClick={() => onSelect(row)}
                className={`cursor-pointer transition-colors ${selectedReport?.id === row.id ? 'bg-primary/5' : 'hover:bg-gray-50'}`}
              >
                <td className="px-6 py-4 text-gray-900 font-medium">{row.name}</td>
                <td className="px-6 py-4 text-gray-500">{row.date}</td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${getRiskColor(row.result)}`}>
                    {row.result}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-primary transition-all" style={{ width: `${row.confidence || 0}%` }}></div>
                    </div>
                    <span className="text-xs font-bold text-gray-600">{row.confidence || 0}%</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-center">
                  <button className="text-primary font-bold hover:underline text-sm">Review</button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center text-gray-500">No records match your search.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-200 flex items-center justify-center gap-2 text-sm">
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(prev => prev - 1)}
            className="p-1 text-gray-500 hover:text-primary disabled:opacity-30 flex items-center"
          >
            <span className="material-symbols-outlined text-lg">chevron_left</span>
          </button>

          <span className="font-medium text-gray-700 px-4">
            Page {currentPage} of {totalPages}
          </span>

          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(prev => prev + 1)}
            className="p-1 text-gray-500 hover:text-primary disabled:opacity-30 flex items-center"
          >
            <span className="material-symbols-outlined text-lg">chevron_right</span>
          </button>
        </div>
      )}
    </div>
  );
}