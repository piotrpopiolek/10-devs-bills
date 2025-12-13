import React from 'react';
import { Badge } from "@/components/ui/badge";

interface SynonymsListProps {
  synonyms: string[];
  maxVisible?: number;
}

export const SynonymsList: React.FC<SynonymsListProps> = ({
  synonyms,
  maxVisible,
}) => {
  if (!synonyms || synonyms.length === 0) {
    return (
      <span className="text-muted-foreground text-sm">-</span>
    );
  }

  const visibleSynonyms = maxVisible
    ? synonyms.slice(0, maxVisible)
    : synonyms;
  const remainingCount = maxVisible && synonyms.length > maxVisible
    ? synonyms.length - maxVisible
    : 0;

  return (
    <div className="flex flex-wrap gap-1">
      {visibleSynonyms.map((synonym, index) => (
        <Badge key={index} variant="outline" className="text-xs">
          {synonym}
        </Badge>
      ))}
      {remainingCount > 0 && (
        <Badge variant="secondary" className="text-xs">
          +{remainingCount}
        </Badge>
      )}
    </div>
  );
};

