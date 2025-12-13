import React from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import type { CategoryTreeNode } from '@/types';

interface CategoryAccordionProps {
  node: CategoryTreeNode;
  level?: number;
}

export const CategoryAccordion: React.FC<CategoryAccordionProps> = ({
  node,
  level = 0,
}) => {
  const hasChildren = node.children && node.children.length > 0;

  return (
    <AccordionItem value={`category-${node.id}`} className="border-b">
      <AccordionTrigger className="hover:no-underline">
        <div className="flex items-center justify-between w-full pr-4">
          <span className="font-medium">{node.name}</span>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {node.products_count > 0 && (
              <Badge variant="secondary" className="text-xs">
                {node.products_count} {node.products_count === 1 ? 'produkt' : 'produktów'}
              </Badge>
            )}
            {node.bill_items_count > 0 && (
              <Badge variant="outline" className="text-xs">
                {node.bill_items_count} {node.bill_items_count === 1 ? 'pozycja' : 'pozycji'}
              </Badge>
            )}
          </div>
        </div>
      </AccordionTrigger>
      {hasChildren && (
        <AccordionContent>
          <div className="pl-4 space-y-1">
            {node.children.map((child) => (
              <CategoryAccordion key={child.id} node={child} level={level + 1} />
            ))}
          </div>
        </AccordionContent>
      )}
      {!hasChildren && (
        <AccordionContent>
          <div className="pl-4 py-2 text-sm text-muted-foreground">
            Brak podkategorii
          </div>
        </AccordionContent>
      )}
    </AccordionItem>
  );
};

