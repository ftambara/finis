# Specifications

Finis is an application to help people manage their expenses and plan their finances. It is offered as a SaaS with private invitations.

## Basis

The application has three main interfaces:
- JSON API
- HTML GUI
- CLI

The first two are client-server based.
The CLI is useful for managing the server. The CLI command is named `fincli` and that is how users invoke it.

## Stack

- Django with Jinja templates
- Django Rest Framework with dataclass extension
- PostgreSQL
- Docker compose for local development (services only; the app is installed on the host)
- Pytest
- HTMX (preferred)
- Vanilla Javascript (when necessary)
- Tailwind CSS
- **`structlog`** for structured logging
- **`environs`** for environment variable management and validation

## Features

### Database Design Philosophy

- **No-Null Schema:** We prioritize database integrity. Nullable and blank fields are almost never allowed. Optional data MUST be handled via related models (e.g., `OneToOneField`) or dedicated link tables.

### Accounts

- Accounts are created on an invitation-basis. We extend invitation links to selected few.
- The administrator can create new accounts using `fincli`.
- Accounts have spending monthly limits according to their tier.
- Spending tiers can be created via CLI. They allow for a maximum monthly token limit.
- Unused spending budget is lost.
- Spending is based on token usage. All interactions with LLMs on behalf of user commands MUST be assigned to that user's organization.
- Organizations group user accounts so they can all, in the future, pay a single bill. They can be created via CLI.

- No billing is supported for now.

### Products

- Users will build their organization product catalog.
- Products have variants along dimensions such as:
    - Format size (weight, size, volume, etc.)
    - Color, flavour, or other types of categorization
    - Brand
- We cannot always assume unit pricing to be dependent only on these factors. There are multiple other things:
    - Volume discounts or other limited-time promotions
    - Seller
    - Time of year
    - Etc.
- What we care about are two perspectives:
    1. Of a product, we'll want to understand certain all nuances about how it was purchased and its specific variant parameters, so that we can do informed decisions when comparing similar products
    2. Hierarchical product categories. Example:
        - Milk, Lactose Free, Fairlife, 8 fl oz
        - Milk
        - Food
- Product hierarchies are trees.
- We'll support different context augmentation procedures, like keeping a local EAN database to do lookups on incomplete product descriptions.
- Some order lines will not be very specific (e.g. groceries). We will have to adapt with whatever level of information the user provides us. We must still be able to categorize that product at an adequate hierarchical level
- When a user adds a product, he or the system will choose a category. He may change it later. When changing a product's category, the system will offer to re-evaluate categories of similar products (all those of the old and those of the new category). This requires LLM API usage.
- Users can obtain a basic view of daily expenses and group by category.


### Scanning

- Users can send pictures of supermarket receipts (or any other type of establishment – we'll keep the models flexible but start by understanding just some formats)
- Receipts can span multiple images.
- Receipts are scanned using Grok Fast API into JSON. We will provide the LLM API with the desired output fields.
- Receipt JSONs are scanned for transaction detail information. Namely:
    - Order information: total price, total discounts, payment method, seller name, seller address, seller-specific order id (formatted as key=value strings separated by spaces and sorted alphabetically), 
    - Order line items: price, product, quantity, discounts
- The information is presented to the customer so he might evaluate the prices
