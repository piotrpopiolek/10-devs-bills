import React, { useMemo } from 'react';
import { useCategories } from '@/components/hooks/useCategories';
import { buildCategoryTree } from '@/lib/utils/category-tree';
import { CategoriesHeader } from './CategoriesHeader';
import { CategoriesTree } from './CategoriesTree';
import { CategoriesLoadingState } from './CategoriesLoadingState';
import { CategoriesErrorState } from './CategoriesErrorState';

export const CategoriesView: React.FC = () => {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useCategories(0, 100);

  // Transform flat list to tree structure
  const treeData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return buildCategoryTree(data);
  }, [data]);

  return (
    <div className="container mx-auto py-10 px-4 md:px-6 space-y-6">
      <CategoriesHeader />

      {isLoading ? (
        <CategoriesLoadingState />
      ) : error ? (
        <CategoriesErrorState error={error} onRetry={refetch} />
      ) : (
        <CategoriesTree treeData={treeData} />
      )}
    </div>
  );
};

