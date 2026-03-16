# # connecting reviews to supabase
# create client 

# create table public.review (
#   review_id uuid not null default gen_random_uuid (),
#   user_id uuid null,
#   product_id uuid null,
#   rating_value integer null,
#   comment text null,
#   date_created timestamp without time zone null default CURRENT_TIMESTAMP,
#   constraint review_pkey primary key (review_id),
#   constraint review_product_id_fkey foreign KEY (product_id) references product (product_id),
#   constraint review_user_id_fkey foreign KEY (user_id) references "user" (user_id)
# ) TABLESPACE pg_default;


