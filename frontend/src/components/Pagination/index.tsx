import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalPages, onPageChange }) => {
  const pageNumbers = [];
  const delta = 2; // Number of pages to show before and after the current page

  for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
    pageNumbers.push(i);
  }

  if (currentPage - delta > 2) {
    pageNumbers.unshift('...');
  }

  if (currentPage + delta < totalPages - 1) {
    pageNumbers.push('...');
  }

  pageNumbers.unshift(1);
  if (totalPages > 1) {
    pageNumbers.push(totalPages);
  }

  return (
    <div className="flex justify-center items-center space-x-2">
      <button onClick={() => onPageChange(1)} disabled={currentPage === 1} className="px-4 py-2 text-sm bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50">First</button>
      <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1} className="px-4 py-2 text-sm bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50">Previous</button>
      {pageNumbers.map((page, index) => (
        page === '...' ? (
          <span key={"page_" + index} className="px-3 py-1 text-sm">...</span>
        ) : (
          <button key={page} onClick={() => onPageChange(page)} disabled={currentPage === page} className={`px-3 py-1 text-sm rounded ${currentPage === page ? 'bg-blue-500 text-white' : 'bg-gray-300 hover:bg-gray-400'}`}>{page}</button>
        )
      ))}
      <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages} className="px-4 py-2 text-sm bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50">Next</button>
      <button onClick={() => onPageChange(totalPages)} disabled={currentPage === totalPages} className="px-4 py-2 text-sm bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50">Last</button>
    </div>
  );
};

export default Pagination;
