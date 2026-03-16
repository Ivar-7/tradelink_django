# # connecting reviews to supabase
# create client 

# create table public.product (
#   product_id uuid not null default gen_random_uuid (),
#   category_id uuid null,
#   product_name text not null,
#   product_description text null,
#   image_url text null,
#   constraint product_pkey primary key (product_id),
#   constraint product_category_id_fkey foreign KEY (category_id) references product_category (category_id)
# ) TABLESPACE pg_default;





