import React from 'react';
import { ChevronRight } from 'lucide-react';
import { BreadcrumbItem } from './AppShell';

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  if (items.length === 0) return null;

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <ChevronRight className="h-4 w-4 text-gray-400 dark:text-gray-500" />
          )}
          {item.isActive ? (
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {item.label}
            </span>
          ) : (
            <button
              onClick={item.onClick}
              className="hover:text-gray-900 dark:hover:text-gray-100 transition-colors duration-200"
            >
              {item.label}
            </button>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};