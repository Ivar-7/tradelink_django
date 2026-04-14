
## 1. Users (Foundation Table)

```sql
INSERT INTO public.user (user_id, username, fname, lname, email_address, password_hash, gender, date_of_birth, role) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'john_doe', 'John', 'Doe', 'john@example.com', '$2b$12$hashedpassword123', 'male', '1990-05-15', 'customer'),
('550e8400-e29b-41d4-a716-446655440001', 'jane_smith', 'Jane', 'Smith', 'jane@example.com', '$2b$12$hashedpassword456', 'female', '1985-08-22', 'customer'),
('550e8400-e29b-41d4-a716-446655440002', 'bob_vendor', 'Bob', 'Williams', 'bob@store.com', '$2b$12$hashedpassword789', 'male', '1988-03-10', 'vendor'),
('550e8400-e29b-41d4-a716-446655440003', 'alice_vendor', 'Alice', 'Johnson', 'alice@shop.com', '$2b$12$hashedpasswordabc', 'female', '1992-11-30', 'vendor'),
('550e8400-e29b-41d4-a716-446655440004', 'charlie_admin', 'Charlie', 'Brown', 'charlie@admin.com', '$2b$12$hashedpassworddef', 'male', '1980-07-05', 'admin');
```

## 2. Pickup Stations (Independent)

```sql
INSERT INTO public.pickup_station (station_id, external_agent_id, name, area, zone, is_active) VALUES
('660e8400-e29b-41d4-a716-446655440000', 'STA001', 'Downtown Central Station', 'CBD', 'Zone A', true),
('660e8400-e29b-41d4-a716-446655440001', 'STA002', 'Westside Mall Pickup', 'Westlands', 'Zone B', true),
('660e8400-e29b-41d4-a716-446655440002', 'STA003', 'Eastgate Express Point', 'Eastleigh', 'Zone C', true),
('660e8400-e29b-41d4-a716-446655440003', 'STA004', 'North Hub Station', 'Kasarani', 'Zone D', true),
('660e8400-e29b-41d4-a716-446655440004', 'STA005', 'Southside Corner', 'Karen', 'Zone E', false);
```

## 3. Product Categories (Self-referencing, parents first)

```sql
INSERT INTO public.product_category (category_id, name, description, parent_id, sort_order) VALUES
('770e8400-e29b-41d4-a716-446655440000', 'Electronics', 'Electronic devices and accessories', NULL, 1),
('770e8400-e29b-41d4-a716-446655440001', 'Clothing', 'Apparel and fashion items', NULL, 2),
('770e8400-e29b-41d4-a716-446655440002', 'Home & Garden', 'Home improvement and garden supplies', NULL, 3),
('770e8400-e29b-41d4-a716-446655440003', 'Smartphones', 'Mobile phones and accessories', '770e8400-e29b-41d4-a716-446655440000', 1),
('770e8400-e29b-41d4-a716-446655440004', 'Laptops', 'Portable computers', '770e8400-e29b-41d4-a716-446655440000', 2);
```

## 4. Vendor Profiles (Depends on users, pickup stations)

```sql
INSERT INTO public.vendor_profile (vendor_id, default_dropoff_station_id, vendor_type, verification_doc_url, is_verified, user_id) VALUES
('880e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'individual', 'https://docs.example.com/bob_id.pdf', true, '550e8400-e29b-41d4-a716-446655440002'),
('880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'business', 'https://docs.example.com/alice_biz.pdf', true, '550e8400-e29b-41d4-a716-446655440003'),
('880e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'individual', 'https://docs.example.com/sam_id.pdf', false, '550e8400-e29b-41d4-a716-446655440000'),
('880e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', 'business', 'https://docs.example.com/tech_corp.pdf', true, '550e8400-e29b-41d4-a716-446655440001'),
('880e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440004', 'individual', NULL, false, '550e8400-e29b-41d4-a716-446655440004');
```

## 5. Vendor Stores (Depends on vendor_profile)

```sql
INSERT INTO public.vendor_store (store_id, vendor_id, store_name, display_name, description, logo_url, banner_url, email_notifications, theme_preference, updated_at) VALUES
('990e8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440000', 'Bob Electronics', 'Bob Tech Shop', 'Quality electronics at great prices', 'https://cdn.example.com/bob_logo.png', 'https://cdn.example.com/bob_banner.jpg', true, 'light', '2024-01-15 10:30:00'),
('990e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 'Alice Fashion', 'Alice Style Boutique', 'Trendy clothing for everyone', 'https://cdn.example.com/alice_logo.png', 'https://cdn.example.com/alice_banner.jpg', true, 'dark', '2024-01-20 14:45:00'),
('990e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 'Sam General Store', 'Sam Marketplace', 'A bit of everything you need', 'https://cdn.example.com/sam_logo.png', 'https://cdn.example.com/sam_banner.jpg', false, 'light', '2024-02-01 09:00:00'),
('990e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440003', 'TechCorp Official', 'TechCorp Store', 'Official electronics retailer', 'https://cdn.example.com/techcorp_logo.png', 'https://cdn.example.com/techcorp_banner.jpg', true, 'light', '2024-01-10 16:20:00'),
('990e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440004', 'Charlie Basics', 'Charlie Essentials', 'Everyday essentials', 'https://cdn.example.com/charlie_logo.png', NULL, true, 'dark', '2024-02-10 11:15:00');
```

## 6. Vendor Wallets (Depends on vendor_profile)

```sql
INSERT INTO public.vendor_wallet (wallet_id, vendor_id, available_balance, pending_balance, currency, updated_at) VALUES
('aa0e8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440000', 15000.50, 2500.00, 'USD', '2024-03-15 08:30:00'),
('aa0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 28500.75, 1200.50, 'USD', '2024-03-14 16:45:00'),
('aa0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 500.00, 150.00, 'USD', '2024-03-10 09:20:00'),
('aa0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440003', 45000.00, 8000.00, 'USD', '2024-03-15 12:00:00'),
('aa0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440004', 0.00, 0.00, 'USD', '2024-03-01 10:00:00');
```

## 7. Products (Depends on product_category, vendor_profile)

```sql
INSERT INTO public.product (product_id, category_id, product_name, product_description, image_url, price, stock, vendor_id) VALUES
('bb0e8400-e29b-41d4-a716-446655440000', '770e8400-e29b-41d4-a716-446655440003', 'iPhone 15 Pro', 'Latest Apple smartphone with titanium design', 'https://cdn.example.com/iphone15.jpg', 999, 50, '880e8400-e29b-41d4-a716-446655440000'),
('bb0e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440004', 'MacBook Air M3', 'Lightweight laptop with M3 chip', 'https://cdn.example.com/macbook_m3.jpg', 1299, 30, '880e8400-e29b-41d4-a716-446655440000'),
('bb0e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001', 'Summer Floral Dress', 'Light cotton dress perfect for summer', 'https://cdn.example.com/floral_dress.jpg', 45, 100, '880e8400-e29b-41d4-a716-446655440001'),
('bb0e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002', 'Garden Tool Set', 'Complete gardening toolkit with 5 tools', 'https://cdn.example.com/garden_set.jpg', 35, 75, '880e8400-e29b-41d4-a716-446655440002'),
('bb0e8400-e29b-41d4-a716-446655440004', '770e8400-e29b-41d4-a716-446655440003', 'Samsung Galaxy S24', 'Android flagship with AI features', 'https://cdn.example.com/galaxy_s24.jpg', 899, 40, '880e8400-e29b-41d4-a716-446655440003');
```

## 8. Stock (Depends on product, vendor_profile)

```sql
INSERT INTO public.stock (stock_id, product_id, vendor_id, quantity, price, is_flash_sale, discount_percentage, last_updated) VALUES
('cc0e8400-e29b-41d4-a716-446655440000', 'bb0e8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440000', 50, 999.00, false, 0, '2024-03-15 10:00:00'),
('cc0e8400-e29b-41d4-a716-446655440001', 'bb0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440000', 30, 1299.00, true, 10, '2024-03-14 09:30:00'),
('cc0e8400-e29b-41d4-a716-446655440002', 'bb0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', 100, 45.00, false, 0, '2024-03-15 11:00:00'),
('cc0e8400-e29b-41d4-a716-446655440003', 'bb0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440002', 75, 35.00, false, 15, '2024-03-10 14:00:00'),
('cc0e8400-e29b-41d4-a716-446655440004', 'bb0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440003', 40, 899.00, true, 5, '2024-03-15 08:00:00');
```

## 9. Delivery Addresses (Depends on user)

```sql
INSERT INTO public.delivery_address (address_id, user_id, country, county, city, postal_address, contact_phone) VALUES
('dd0e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'USA', 'New York', 'New York City', '123 Broadway, Apt 4B, NY 10001', '+1-555-0101'),
('dd0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'USA', 'California', 'Los Angeles', '456 Sunset Blvd, LA 90028', '+1-555-0102'),
('dd0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 'USA', 'Texas', 'Austin', '789 Congress Ave, Austin 78701', '+1-555-0103'),
('dd0e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'Canada', 'Ontario', 'Toronto', '321 Yonge St, Toronto M5B 2S1', '+1-555-0104'),
('dd0e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'UK', 'Greater London', 'London', '654 Oxford Street, London W1D 1LR', '+44-555-0105');
```

## 10. Carts (Depends on user)

```sql
INSERT INTO public.cart (cart_id, user_id, date_created, total_price) VALUES
('ee0e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', '2024-03-15 09:00:00', 1044.00),
('ee0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '2024-03-14 15:30:00', 90.00),
('ee0e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', '2024-03-15 10:00:00', 35.00),
('ee0e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', '2024-03-13 11:00:00', 1299.00),
('ee0e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', '2024-03-12 14:00:00', 45.00);
```

## 11. Cart Items (Depends on cart, stock)

```sql
INSERT INTO public.cart_item (cart_item_id, cart_id, stock_id, quantity) VALUES
('ff0e8400-e29b-41d4-a716-446655440000', 'ee0e8400-e29b-41d4-a716-446655440000', 'cc0e8400-e29b-41d4-a716-446655440000', 1),
('ff0e8400-e29b-41d4-a716-446655440001', 'ee0e8400-e29b-41d4-a716-446655440000', 'cc0e8400-e29b-41d4-a716-446655440003', 3),
('ff0e8400-e29b-41d4-a716-446655440002', 'ee0e8400-e29b-41d4-a716-446655440001', 'cc0e8400-e29b-41d4-a716-446655440002', 2),
('ff0e8400-e29b-41d4-a716-446655440003', 'ee0e8400-e29b-41d4-a716-446655440003', 'cc0e8400-e29b-41d4-a716-446655440001', 1),
('ff0e8400-e29b-41d4-a716-446655440004', 'ee0e8400-e29b-41d4-a716-446655440004', 'cc0e8400-e29b-41d4-a716-446655440002', 1);
```

## 12. Orders (Depends on user, delivery_address, pickup_station)

```sql
INSERT INTO public.orders (order_id, user_id, address_id, station_id, shipping_type, order_date, total_amount, status) VALUES
('001f8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'dd0e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'pickup', '2024-03-10 14:30:00', 1044.00, 'delivered'),
('001f8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'dd0e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'delivery', '2024-03-12 10:00:00', 90.00, 'shipped'),
('001f8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 'dd0e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440002', 'pickup', '2024-03-14 16:00:00', 1299.00, 'packed'),
('001f8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'dd0e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440003', 'delivery', '2024-03-15 09:00:00', 45.00, 'confirmed'),
('001f8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'dd0e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440004', 'pickup', '2024-03-15 11:30:00', 899.00, 'pending');
```

## 13. Order Suborders (Depends on orders, vendor_profile)

```sql
INSERT INTO public.order_suborder (suborder_id, order_id, vendor_id, subtotal, status, created_at) VALUES
('112f8400-e29b-41d4-a716-446655440000', '001f8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440000', 999.00, 'delivered', '2024-03-10 14:30:00'),
('112f8400-e29b-41d4-a716-446655440001', '001f8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440002', 45.00, 'delivered', '2024-03-10 14:30:00'),
('112f8400-e29b-41d4-a716-446655440002', '001f8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 90.00, 'shipped', '2024-03-12 10:00:00'),
('112f8400-e29b-41d4-a716-446655440003', '001f8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440000', 1299.00, 'packed', '2024-03-14 16:00:00'),
('112f8400-e29b-41d4-a716-446655440004', '001f8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001', 45.00, 'confirmed', '2024-03-15 09:00:00');
```

## 14. Order Items (Depends on orders, stock, vendor_profile)

```sql
INSERT INTO public.order_item (order_item_id, order_id, stock_id, quantity, unit_price, vendor_id) VALUES
('223f8400-e29b-41d4-a716-446655440000', '001f8400-e29b-41d4-a716-446655440000', 'cc0e8400-e29b-41d4-a716-446655440000', 1, 999.00, '880e8400-e29b-41d4-a716-446655440000'),
('223f8400-e29b-41d4-a716-446655440001', '001f8400-e29b-41d4-a716-446655440000', 'cc0e8400-e29b-41d4-a716-446655440003', 3, 15.00, '880e8400-e29b-41d4-a716-446655440002'),
('223f8400-e29b-41d4-a716-446655440002', '001f8400-e29b-41d4-a716-446655440001', 'cc0e8400-e29b-41d4-a716-446655440002', 2, 45.00, '880e8400-e29b-41d4-a716-446655440001'),
('223f8400-e29b-41d4-a716-446655440003', '001f8400-e29b-41d4-a716-446655440002', 'cc0e8400-e29b-41d4-a716-446655440001', 1, 1299.00, '880e8400-e29b-41d4-a716-446655440000'),
('223f8400-e29b-41d4-a716-446655440004', '001f8400-e29b-41d4-a716-446655440003', 'cc0e8400-e29b-41d4-a716-446655440002', 1, 45.00, '880e8400-e29b-41d4-a716-446655440001');
```

## 15. Payments (Depends on orders, user)

```sql
INSERT INTO public.payment (payment_id, order_id, user_id, amount, payment_provider, transaction_reference, status) VALUES
('334f8400-e29b-41d4-a716-446655440000', '001f8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 1044.00, 'stripe', 'pi_3Osample123', 'completed'),
('334f8400-e29b-41d4-a716-446655440001', '001f8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 90.00, 'paypal', 'PAY-SAMPLE-456', 'completed'),
('334f8400-e29b-41d4-a716-446655440002', '001f8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 1299.00, 'stripe', 'pi_3Osample789', 'completed'),
('334f8400-e29b-41d4-a716-446655440003', '001f8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 45.00, 'stripe', 'pi_3OsampleABC', 'pending'),
('334f8400-e29b-41d4-a716-446655440004', '001f8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 899.00, 'mpesa', 'MPESA123456', 'completed');
```

## 16. Shipments (Depends on orders)

```sql
INSERT INTO public.shipment (shipment_id, order_id, external_package_id, tracking_number, delivery_fee, status, last_update_time) VALUES
('445f8400-e29b-41d4-a716-446655440000', '001f8400-e29b-41d4-a716-446655440000', 'PKG001234', 'TRK999000111', 5.00, 'delivered', '2024-03-12 10:00:00'),
('445f8400-e29b-41d4-a716-446655440001', '001f8400-e29b-41d4-a716-446655440001', 'PKG001235', 'TRK999000112', 8.00, 'in_transit', '2024-03-14 16:00:00'),
('445f8400-e29b-41d4-a716-446655440002', '001f8400-e29b-41d4-a716-446655440002', 'PKG001236', 'TRK999000113', 0.00, 'ready_for_pickup', '2024-03-15 09:00:00'),
('445f8400-e29b-41d4-a716-446655440003', '001f8400-e29b-41d4-a716-446655440003', 'PKG001237', 'TRK999000114', 6.00, 'label_created', '2024-03-15 11:00:00'),
('445f8400-e29b-41d4-a716-446655440004', '001f8400-e29b-41d4-a716-446655440004', NULL, NULL, 0.00, 'pending', '2024-03-15 11:30:00');
```

## 17. Reviews (Depends on user, product)

```sql
INSERT INTO public.review (review_id, user_id, product_id, rating_value, comment, date_created) VALUES
('556f8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'bb0e8400-e29b-41d4-a716-446655440000', 5, 'Excellent phone, fast delivery!', '2024-03-12 09:00:00'),
('556f8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'bb0e8400-e29b-41d4-a716-446655440002', 4, 'Nice dress, slightly small fit', '2024-03-13 14:00:00'),
('556f8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 'bb0e8400-e29b-41d4-a716-446655440001', 5, 'MacBook is amazing for work', '2024-03-15 10:00:00'),
('556f8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'bb0e8400-e29b-41d4-a716-446655440003', 3, 'Tools are okay, handle could be better', '2024-03-11 16:00:00'),
('556f8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'bb0e8400-e29b-41d4-a716-446655440004', 4, 'Great Android phone, good camera', '2024-03-16 08:00:00');
```

## 18. Inventory Movements (Depends on stock)

```sql
INSERT INTO public.inventory_movement (movement_id, stock_id, movement_type, quantity_change, previous_quantity, new_quantity, reference_id, created_at) VALUES
('667f8400-e29b-41d4-a716-446655440000', 'cc0e8400-e29b-41d4-a716-446655440000', 'sale', -1, 51, 50, '223f8400-e29b-41d4-a716-446655440000', '2024-03-10 14:30:00'),
('667f8400-e29b-41d4-a716-446655440001', 'cc0e8400-e29b-41d4-a716-446655440003', 'sale', -3, 78, 75, '223f8400-e29b-41d4-a716-446655440001', '2024-03-10 14:30:00'),
('667f8400-e29b-41d4-a716-446655440002', 'cc0e8400-e29b-41d4-a716-446655440002', 'sale', -2, 102, 100, '223f8400-e29b-41d4-a716-446655440002', '2024-03-12 10:00:00'),
('667f8400-e29b-41d4-a716-446655440003', 'cc0e8400-e29b-41d4-a716-446655440001', 'sale', -1, 31, 30, '223f8400-e29b-41d4-a716-446655440003', '2024-03-14 16:00:00'),
('667f8400-e29b-41d4-a716-446655440004', 'cc0e8400-e29b-41d4-a716-446655440002', 'restock', 50, 50, 100, NULL, '2024-03-01 08:00:00');
```

## 19. Vendor Payouts (Depends on vendor_profile)

```sql
INSERT INTO public.vendor_payouts (payout_id, vendor_id, amount, status, payout_method, reference_code, requested_at, processed_at) VALUES
('778f8400-e29b-41d4-a716-446655440000', '880e8400-e29b-41d4-a716-446655440000', 5000.00, 'completed', 'bank_transfer', 'PAYOUT001', '2024-03-01 10:00:00', '2024-03-03 14:00:00'),
('778f8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 8000.00, 'completed', 'bank_transfer', 'PAYOUT002', '2024-03-05 09:00:00', '2024-03-07 11:00:00'),
('778f8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440000', 3000.00, 'pending', 'mobile_money', 'PAYOUT003', '2024-03-15 08:00:00', NULL),
('778f8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440003', 12000.00, 'completed', 'bank_transfer', 'PAYOUT004', '2024-03-10 16:00:00', '2024-03-12 10:00:00'),
('778f8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440001', 2500.00, 'processing', 'paypal', 'PAYOUT005', '2024-03-14 13:00:00', NULL);
```

## 20. User Feedback (Depends on user)

```sql
INSERT INTO public.user_feedback (feedback_id, user_id, type, message, date_submitted) VALUES
('889f8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 'bug_report', 'App crashes when adding item to cart on mobile', '2024-03-10 11:00:00'),
('889f8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'feature_request', 'Would love dark mode for the website', '2024-03-12 15:00:00'),
('889f8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 'complaint', 'Delivery was late by 2 days', '2024-03-14 09:00:00'),
('889f8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'compliment', 'Great vendor, fast shipping!', '2024-03-15 10:00:00'),
('889f8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'general', 'How do I become a vendor?', '2024-03-16 08:00:00');
```

---

## Insertion Order Summary

| Order | Table | Dependencies |
|-------|-------|-------------|
| 1 | `user` | None |
| 2 | `pickup_station` | None |
| 3 | `product_category` | None (self-referencing) |
| 4 | `vendor_profile` | user, pickup_station |
| 5 | `vendor_store` | vendor_profile |
| 6 | `vendor_wallet` | vendor_profile |
| 7 | `product` | product_category, vendor_profile |
| 8 | `stock` | product, vendor_profile |
| 9 | `delivery_address` | user |
| 10 | `cart` | user |
| 11 | `cart_item` | cart, stock |
| 12 | `orders` | user, delivery_address, pickup_station |
| 13 | `order_suborder` | orders, vendor_profile |
| 14 | `order_item` | orders, stock, vendor_profile |
| 15 | `payment` | orders, user |
| 16 | `shipment` | orders |
| 17 | `review` | user, product |
| 18 | `inventory_movement` | stock |
| 19 | `vendor_payouts` | vendor_profile |
| 20 | `user_feedback` | user |

