# E-Commerce Data Generator

Synthetic e-commerce dataset generator for big data pipelines. Produces CSV files for four relational tables: `customers`, `products`, `orders`, and `order_items`.

> **Note**: The code in this repository is based on [NaelAqel/db_gen](https://github.com/NaelAqel/db_gen).

## Schema

| Table       | Key Columns                                                                       |
| ----------- | --------------------------------------------------------------------------------- |
| customers   | customer_id, name, email, gender, signup_date, country                            |
| products    | product_id, product_name, category, price, stock_quantity, brand                  |
| orders      | order_id, customer_id, order_date, total_amount, payment_method, shipping_country |
| order_items | order_item_id, order_id, product_id, quantity, unit_price                         |

## Usage

### Setup (recommended)

Even though dependencies are installed automatically, it is recommended to run the script inside a virtual environment to keep your system Python clean:

```bash
python -m venv .venv

source .venv/bin/activate  # on macOS/Linux
```

### Install dependencies

Dependencies are installed automatically on first run. Requires Python 3.8+ and `pip`.

### Run with default values

```bash
python dataset_generator.py
```

### Run with custom values

```bash
python dataset_generator.py \
    --customers 6000 \
    --products 2000 \
    --orders 1000000 \
    --order-items 4000000 \
    --path data \
    --chunk-size 1000000
```

## CLI Arguments

| Argument        | Default   | Description              |
| --------------- | --------- | ------------------------ |
| `--customers`   | 6,000     | Number of customers      |
| `--products`    | 2,000     | Number of products       |
| `--orders`      | 1,000,000 | Number of orders         |
| `--order-items` | 4,000,000 | Number of order items    |
| `--path`        | `data/`   | Output directory         |
| `--chunk-size`  | 1,000,000 | Number of rows per chunk |

## Output Structure

```
data/
  customers/
    part_0000.csv
  products/
    part_0000.csv
  orders/
    part_0000.csv
    part_0001.csv
    ...
  order_items/
    part_0000.csv
    part_0001.csv
    ...
```

Each table is split into part files of `--chunk-size` rows. This matches how Spark reads directories of files natively.

## Performance Notes

Generating customers and products is the most resource-intensive task. Both tables rely on [Faker](https://faker.readthedocs.io/) to produce realistic names, emails, and product names, that is, one Python call per row. Keep these counts as low as your use case allows and scale `--orders` and `--order-items` instead to reach your target dataset size.

For reference, on a modern laptop:

- 6,000 customers + 2,000 products + 1M orders + 4M order items ≈ **~19 seconds**, ~160 MB
- To reach ~30 GB, scale orders to ~250,000,000 and order-items to ~625,000,000.
