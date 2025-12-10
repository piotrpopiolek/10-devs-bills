-- ============================================================================
-- Migration: Seed predefined product categories
-- ============================================================================
-- Purpose: Inserts all predefined product categories and subcategories
--          into the categories table with proper hierarchical structure.
--
-- Affected objects:
--   - Table: categories
--
-- Special considerations:
--   - Categories are inserted in two steps: first main categories, then subcategories
--   - Uses CTE to reference parent category IDs when inserting subcategories
--   - Comments in parentheses (e.g., "Produkty Sypkie (mąka, cukier...)") are removed
--   - The "Inne" category is the default category for uncategorized products
-- ============================================================================

-- Insert main categories (parent_id = NULL)
-- These are the top-level categories in the hierarchy

insert into categories (name, parent_id) values
    ('Jedzenie i Napoje', null),
    ('Transport', null),
    ('Zdrowie i Uroda', null),
    ('Dom i Ogród', null),
    ('Odzież i Obuwie', null),
    ('Elektronika', null),
    ('Rozrywka', null),
    ('Usługi', null),
    ('Zwierzęta Domowe', null),
    ('Prezenty i Kwiaty', null),
    ('Wyroby Tytoniowe', null),
    ('Inne', null)
on conflict (name) do nothing;

-- Insert subcategories for "Jedzenie i Napoje"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Jedzenie i Napoje' limit 1) as parent_id
from (values
    ('Pieczywo'),
    ('Nabiał i Jaja'),
    ('Mięso i Wędliny'),
    ('Ryby i Owoce Morza'),
    ('Warzywa'),
    ('Owoce'),
    ('Napoje'),
    ('Słodycze i Przekąski'),
    ('Produkty Sypkie'),
    ('Konserwy i Przetwory'),
    ('Mrożonki'),
    ('Alkohol'),
    ('Restauracje i Jedzenie na Wynos')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Transport"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Transport' limit 1) as parent_id
from (values
    ('Paliwo'),
    ('Bilety Komunikacji Miejskiej'),
    ('Parking'),
    ('Myjnia Samochodowa'),
    ('Naprawy i Serwis Samochodu'),
    ('Części Samochodowe')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Zdrowie i Uroda"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Zdrowie i Uroda' limit 1) as parent_id
from (values
    ('Leki i Suplementy'),
    ('Kosmetyki'),
    ('Środki Higieniczne'),
    ('Sprzęt Medyczny'),
    ('Pieluchy i Produkty dla Niemowląt')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Dom i Ogród"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Dom i Ogród' limit 1) as parent_id
from (values
    ('Chemia Gospodarcza'),
    ('Artykuły Papiernicze'),
    ('Narzędzia'),
    ('Rośliny i Nasiona'),
    ('Meble i Dekoracje'),
    ('Oświetlenie')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Odzież i Obuwie"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Odzież i Obuwie' limit 1) as parent_id
from (values
    ('Odzież Męska'),
    ('Odzież Damska'),
    ('Odzież Dziecięca'),
    ('Odzież Sportowa'),
    ('Obuwie'),
    ('Akcesoria')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Elektronika"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Elektronika' limit 1) as parent_id
from (values
    ('Telefony i Akcesoria'),
    ('Komputery i Akcesoria'),
    ('AGD'),
    ('Baterie i Ładowarki')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Rozrywka"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Rozrywka' limit 1) as parent_id
from (values
    ('Książki i Czasopisma'),
    ('Gry i Zabawki'),
    ('Kino i Wydarzenia'),
    ('Hobby i Rękodzieło'),
    ('Sport i Fitness')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Usługi"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Usługi' limit 1) as parent_id
from (values
    ('Fryzjer i Kosmetyczka'),
    ('Naprawy'),
    ('Czyszczenie'),
    ('Edukacja i Kursy'),
    ('Komunikacja'),
    ('Bankowość i Finanse')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Zwierzęta Domowe"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Zwierzęta Domowe' limit 1) as parent_id
from (values
    ('Karma dla Zwierząt'),
    ('Akcesoria dla Zwierząt'),
    ('Weterynaria')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Prezenty i Kwiaty"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Prezenty i Kwiaty' limit 1) as parent_id
from (values
    ('Kwiaty'),
    ('Prezenty i Kartki'),
    ('Dekoracje Okolicznościowe')
) as subcat(name)
on conflict (name) do nothing;

-- Insert subcategories for "Wyroby Tytoniowe"
insert into categories (name, parent_id)
select 
    subcat.name,
    (select id from categories where name = 'Wyroby Tytoniowe' limit 1) as parent_id
from (values
    ('Papierosy'),
    ('E-papierosy i Akcesoria'),
    ('Tytoń')
) as subcat(name)
on conflict (name) do nothing;

-- Note: "Inne" category has no subcategories and serves as the default category
-- for products that don't fit into any other category

