Tradelink Discussion Ideas:
Businesses and Individuals can be vendors.
How to handle logistics? Pick up mtaani
Flash Sale

TRADELINK USER SCOPE:
Country, Kenya
Include anything that can be bought except food
Businesses and Individuals can be vendors.

TRADELINK UML DIAGRAMS:
Usecase Diagram:
Buyer, Vendor and Admin usecases

Buyer actions:
sign up
search products
place order
confirm prodect delivery
rate products
browsing product
pay for product
track order
cancel order

Vendor:
register
upload verification documents
upload product
update stock
edit product
delete product
create/offer discounts
withdraw funds


Class Diagrams:
USER:
user_id
username
user_fname
user_lname
user_email
user_password
user_gender
user_dob
user_role
user_cart


PRODUCT
id
name
price
description
catgory_id
stock_quantity
image_url

ORDER
id
user_id
order_date
order_amount
products
status
shipping method

CART
id
user_id
date_created
total_price
products

PAYMENT(transaction type included)
id
user_id
order_id
amount
payment_provider
status

REVIEW(rating and product review)
id
user_id
product_id
rating_value
comment
date

USERFEEDBACK
id
user_id
type
message

DELIVERYADDRESS
country
county
city
postal_address
user_email
user_contact

Sequence Diagram:

Activity Diagram: