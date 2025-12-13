import React from 'react';
import { Accordion } from '@/components/ui/accordion';
import { CategoryAccordion } from './CategoryAccordion';
import type { CategoryTreeNode } from '@/types';

interface CategoriesTreeProps {
  treeData: CategoryTreeNode[];
}

export const CategoriesTree: React.FC<CategoriesTreeProps> = ({ treeData }) => {
  if (!treeData || treeData.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground">Nie znaleziono kategorii</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Accordion type="multiple" className="w-full">
        {treeData.map((node) => (
          <CategoryAccordion key={node.id} node={node} />
        ))}
      </Accordion>
    </div>
  );
};

