import React from 'react';

export const CategoriesHeader: React.FC = () => {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-3xl font-bold tracking-tight">Kategorie</h1>
      <p className="text-muted-foreground">
        Wizualizacja hierarchii wydatków
      </p>
    </div>
  );
};

