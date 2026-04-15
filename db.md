-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.cart (
  cart_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  date_created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  total_price numeric,
  CONSTRAINT cart_pkey PRIMARY KEY (cart_id),
  CONSTRAINT cart_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.cart_item (
  cart_item_id uuid NOT NULL DEFAULT gen_random_uuid(),
  cart_id uuid,
  stock_id uuid,
  quantity integer,
  CONSTRAINT cart_item_pkey PRIMARY KEY (cart_item_id),
  CONSTRAINT cart_item_cart_id_fkey FOREIGN KEY (cart_id) REFERENCES public.cart(cart_id),
  CONSTRAINT cart_item_stock_id_fkey FOREIGN KEY (stock_id) REFERENCES public.stock(stock_id)
);
CREATE TABLE public.delivery_address (
  address_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  country text,
  county text,
  city text,
  postal_address text,
  contact_phone text,
  CONSTRAINT delivery_address_pkey PRIMARY KEY (address_id),
  CONSTRAINT delivery_address_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.inventory_movement (
  movement_id uuid NOT NULL DEFAULT gen_random_uuid(),
  stock_id uuid,
  movement_type text,
  quantity_change integer,
  previous_quantity integer,
  new_quantity integer,
  reference_id uuid,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT inventory_movement_pkey PRIMARY KEY (movement_id),
  CONSTRAINT inventory_movement_stock_id_fkey FOREIGN KEY (stock_id) REFERENCES public.stock(stock_id)
);
CREATE TABLE public.order_item (
  order_item_id uuid NOT NULL DEFAULT gen_random_uuid(),
  order_id uuid,
  stock_id uuid,
  quantity integer,
  unit_price numeric,
  vendor_id uuid,
  CONSTRAINT order_item_pkey PRIMARY KEY (order_item_id),
  CONSTRAINT order_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id),
  CONSTRAINT order_item_stock_id_fkey FOREIGN KEY (stock_id) REFERENCES public.stock(stock_id),
  CONSTRAINT order_item_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);
CREATE TABLE public.order_suborder (
  suborder_id uuid NOT NULL DEFAULT gen_random_uuid(),
  order_id uuid,
  vendor_id uuid,
  subtotal numeric,
  status text,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT order_suborder_pkey PRIMARY KEY (suborder_id),
  CONSTRAINT order_suborder_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id),
  CONSTRAINT order_suborder_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);
CREATE TABLE public.orders (
  order_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  address_id uuid,
  station_id uuid,
  shipping_type text,
  order_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  total_amount numeric,
  status text,
  CONSTRAINT orders_pkey PRIMARY KEY (order_id),
  CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id),
  CONSTRAINT orders_address_id_fkey FOREIGN KEY (address_id) REFERENCES public.delivery_address(address_id),
  CONSTRAINT orders_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.pickup_station(station_id)
);
CREATE TABLE public.payment (
  payment_id uuid NOT NULL DEFAULT gen_random_uuid(),
  order_id uuid,
  user_id uuid,
  amount numeric,
  payment_provider text,
  transaction_reference text,
  status text,
  CONSTRAINT payment_pkey PRIMARY KEY (payment_id),
  CONSTRAINT payment_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id),
  CONSTRAINT payment_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.pickup_station (
  station_id uuid NOT NULL DEFAULT gen_random_uuid(),
  external_agent_id text,
  name text NOT NULL,
  area text,
  zone text,
  is_active boolean DEFAULT true,
  CONSTRAINT pickup_station_pkey PRIMARY KEY (station_id)
);
CREATE TABLE public.product (
  product_id uuid NOT NULL DEFAULT gen_random_uuid(),
  category_id uuid,
  product_name text NOT NULL,
  product_description text,
  image_url text,
  price smallint,
  stock smallint,
  vendor_id uuid,
  CONSTRAINT product_pkey PRIMARY KEY (product_id),
  CONSTRAINT product_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_category(category_id),
  CONSTRAINT product_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);
CREATE TABLE public.product_category (
  category_id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  parent_id uuid,
  sort_order integer DEFAULT 0,
  CONSTRAINT product_category_pkey PRIMARY KEY (category_id),
  CONSTRAINT product_category_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.product_category(category_id)
);
CREATE TABLE public.review (
  review_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  product_id uuid,
  rating_value integer,
  comment text,
  date_created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT review_pkey PRIMARY KEY (review_id),
  CONSTRAINT review_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(product_id),
  CONSTRAINT review_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.shipment (
  shipment_id uuid NOT NULL DEFAULT gen_random_uuid(),
  order_id uuid,
  external_package_id text,
  tracking_number text,
  delivery_fee numeric,
  status text,
  last_update_time timestamp without time zone,
  CONSTRAINT shipment_pkey PRIMARY KEY (shipment_id),
  CONSTRAINT shipment_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id)
);
CREATE TABLE public.stock (
  stock_id uuid NOT NULL DEFAULT gen_random_uuid(),
  product_id uuid,
  vendor_id uuid,
  quantity integer,
  price numeric,
  is_flash_sale boolean DEFAULT false,
  discount_percentage numeric,
  last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT stock_pkey PRIMARY KEY (stock_id),
  CONSTRAINT stock_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id),
  CONSTRAINT stock_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.product(product_id)
);
CREATE TABLE public.user (
  user_id uuid NOT NULL DEFAULT gen_random_uuid(),
  username text UNIQUE,
  fname text,
  lname text,
  email_address text UNIQUE,
  password_hash text,
  gender text,
  date_of_birth date,
  role text,
  CONSTRAINT user_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.user_feedback (
  feedback_id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  type text,
  message text,
  date_submitted timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT user_feedback_pkey PRIMARY KEY (feedback_id),
  CONSTRAINT user_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.vendor_payouts (
  payout_id uuid NOT NULL DEFAULT gen_random_uuid(),
  vendor_id uuid,
  amount numeric NOT NULL,
  status text DEFAULT 'pending'::text,
  payout_method text,
  reference_code text,
  requested_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  processed_at timestamp without time zone,
  CONSTRAINT vendor_payouts_pkey PRIMARY KEY (payout_id),
  CONSTRAINT vendor_payouts_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);
CREATE TABLE public.vendor_profile (
  vendor_id uuid NOT NULL DEFAULT gen_random_uuid(),
  default_dropoff_station_id uuid,
  vendor_type text,
  verification_doc_url text,
  is_verified boolean DEFAULT false,
  user_id uuid UNIQUE,
  CONSTRAINT vendor_profile_pkey PRIMARY KEY (vendor_id),
  CONSTRAINT vendor_profile_default_dropoff_station_id_fkey FOREIGN KEY (default_dropoff_station_id) REFERENCES public.pickup_station(station_id),
  CONSTRAINT vendor_profile_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(user_id)
);
CREATE TABLE public.vendor_store (
  store_id uuid NOT NULL DEFAULT gen_random_uuid(),
  vendor_id uuid UNIQUE,
  store_name text NOT NULL,
  display_name text,
  description text,
  logo_url text,
  banner_url text,
  email_notifications boolean DEFAULT true,
  theme_preference text DEFAULT 'light'::text,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT vendor_store_pkey PRIMARY KEY (store_id),
  CONSTRAINT vendor_store_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);
CREATE TABLE public.vendor_wallet (
  wallet_id uuid NOT NULL DEFAULT gen_random_uuid(),
  vendor_id uuid UNIQUE,
  available_balance numeric DEFAULT 0,
  pending_balance numeric DEFAULT 0,
  currency text DEFAULT 'USD'::text,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT vendor_wallet_pkey PRIMARY KEY (wallet_id),
  CONSTRAINT vendor_wallet_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendor_profile(vendor_id)
);