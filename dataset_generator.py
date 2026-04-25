import argparse
import importlib
from pathlib import Path
import random
import subprocess
import sys

COUNTRIES = [
    'United States', 'Germany', 'Brazil', 'Japan', 'United Kingdom',
    'France', 'Canada', 'Australia', 'India', 'Mexico',
]

def check_package(package_name, import_name=None):
    """
    Check and install the package if it does not exist (to avoid ImportError).

    Args:
        package_name (str): Package name to install via pip.
        import_name (str, optional): Import name if different from package_name.
    """

    import_name = import_name or package_name

    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f'Installing {package_name}...')

        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package_name])

        print(f'\nPlease restart the script after {package_name} installation.\n')

        sys.exit(0)
    # end try-except
# end def

def generate_customers(n, pd, np, fake):
    """
    Returns n rows of customers data as a DataFrame.

    Args:
        n (int): Number of customer rows to generate.
        pd: pandas module.
        np: numpy module.
        fake (Faker): Faker instance.

    Returns:
        pd.DataFrame: Customers DataFrame.
    """

    start = np.datetime64('today') - np.timedelta64(5 * 365, 'D')
    offsets = np.random.randint(0, 5 * 365, size=n)
    dates = (start + offsets.astype('timedelta64[D]')).astype(str)

    return pd.DataFrame({
        'customer_id': range(1, n + 1),
        'name': [fake.name() for _ in range(n)],
        'email': [fake.email() for _ in range(n)],
        'gender': np.random.choice(['Male', 'Female', 'Other'], size=n),
        'signup_date': dates,
        'country': np.random.choice(COUNTRIES, size=n),
    })
# end def

def generate_products(n, pd, fake):
    """
    Returns n rows of products data as a DataFrame.

    Args:
        n (int): Number of product rows to generate.
        pd: pandas module.
        fake (Faker): Faker instance.

    Returns:
        pd.DataFrame: Products DataFrame.
    """

    categories = ['Electronics', 'Books', 'Clothing', 'Toys', 'Home', 'Beauty']
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD']

    return pd.DataFrame([{
        'product_id': i,
        'product_name': fake.word().capitalize() + ' ' + fake.word().capitalize(),
        'category': random.choice(categories),
        'price': round(random.uniform(5.0, 500.0), 2),
        'stock_quantity': random.randint(0, 1000),
        'brand': random.choice(brands),
    } for i in range(1, n + 1)])
# end def

def generate_orders_chunk(chunk_id, n, id_offset, customer_ids, pd, np):
    """
    Returns a chunk of n orders rows as a DataFrame, with IDs starting at id_offset.

    Args:
        chunk_id (int): Index of the current chunk (unused in logic, kept for consistency).
        n (int): Number of rows in this chunk.
        id_offset (int): Starting order_id for this chunk.
        customer_ids (np.ndarray): Array of valid customer IDs to sample from.
        pd: pandas module.
        np: numpy module.

    Returns:
        pd.DataFrame: Orders chunk DataFrame.
    """

    start = np.datetime64('today') - np.timedelta64(4 * 365, 'D')
    offsets = np.random.randint(0, 4 * 365, size=n)
    dates = (start + offsets.astype('timedelta64[D]')).astype(str)

    return pd.DataFrame({
        'order_id': range(id_offset, id_offset + n),
        'customer_id': np.random.choice(customer_ids, size=n),
        'order_date': dates,
        'total_amount': np.zeros(n),  # fills in after order_items are generated
        'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash'], size=n),
        'shipping_country': np.random.choice(COUNTRIES, size=n),
    })

def generate_order_items_chunk(chunk_id, n, id_offset, order_ids, product_ids, price_lookup, pd, np):
    """
    Returns a chunk of n order_items rows as a DataFrame using vectorized numpy ops.

    Args:
        chunk_id (int): Index of the current chunk (unused in logic, kept for consistency).
        n (int): Number of rows in this chunk.
        id_offset (int): Starting order_item_id for this chunk.
        order_ids (np.ndarray): Array of valid order IDs to sample from.
        product_ids (np.ndarray): Array of valid product IDs to sample from.
        price_lookup (np.ndarray): Array indexed by product_id for O(1) price lookup.
        pd: pandas module.
        np: numpy module.

    Returns:
        pd.DataFrame: Order items chunk DataFrame.
    """

    sampled_order_ids = np.random.choice(order_ids, size=n)
    sampled_product_ids = np.random.choice(product_ids, size=n)
    quantities = np.random.randint(1, 6, size=n)
    unit_prices = price_lookup[sampled_product_ids]

    return pd.DataFrame({
        'order_item_id': range(id_offset, id_offset + n),
        'order_id': sampled_order_ids,
        'product_id': sampled_product_ids,
        'quantity': quantities,
        'unit_price': unit_prices,
    })
# end def

def write_chunk(df, path, table_name, chunk_id):
    """
    Writes a DataFrame chunk to CSV.

    Args:
        df (pd.DataFrame): DataFrame to write.
        path (Path): Base output directory.
        table_name (str): Subdirectory name for the table.
        chunk_id (int): Chunk index, used to name the output file.
    """

    out = path / table_name / f'part_{chunk_id:04d}.csv'

    df.to_csv(out, index=False)
# end def

def main(
    num_customers, num_products, num_orders,
    num_order_items, path, chunk_size
):
    """
    Orchestrates the dataset generation pipeline.

    Args:
        num_customers (int): Number of customer rows to generate.
        num_products (int): Number of product rows to generate.
        num_orders (int): Total number of order rows to generate.
        num_order_items (int): Total number of order item rows to generate.
        path (Path): Base output directory.
        chunk_size (int): Number of rows per output file chunk.
    """
    # checks and imports dependencies
    check_package('Faker', 'faker')
    check_package('pandas')

    # imports dependencies
    from faker import Faker
    import pandas as pd
    import numpy as np

    fake = Faker()

    # creates output directories
    for table in ['customers', 'products', 'orders', 'order_items']:
        (path / table).mkdir(parents=True, exist_ok=True)
    # end for-in

    # generates and writes customers
    print('[1/4] Generating customers...')

    customers_df = generate_customers(num_customers, pd, np, fake)

    customers_df.to_csv(path / 'customers' / 'part_0000.csv', index=False)

    customer_ids = customers_df['customer_id'].to_numpy()

    print(f'      Customers generated ({num_customers:,} rows)')

    # generates and writes products
    print('[2/4] Generating products...')

    products_df = generate_products(num_products, pd, fake)

    products_df.to_csv(path / 'products' / 'part_0000.csv', index=False)
    
    product_ids = products_df['product_id'].to_numpy()

    # builds a numpy array indexed by product_id for O(1) price lookup
    price_lookup = np.zeros(product_ids.max() + 1)
    price_lookup[products_df['product_id'].to_numpy()] = products_df['price'].to_numpy()
    print(f'      Products generated ({num_products:,} rows)')

    # generates and writes orders in chunks
    print('[3/4] Generating orders...')

    # pre-allocates a fixed-size array of order IDs to avoid memory growth
    order_ids_np = np.arange(1, num_orders + 1)
    id_offset = 1
    chunk_id = 0
    remaining = num_orders

    while remaining > 0:
        n = min(chunk_size, remaining)

        chunk = generate_orders_chunk(chunk_id, n, id_offset, customer_ids, pd, np)

        write_chunk(chunk, path, 'orders', chunk_id)

        id_offset += n
        remaining -= n
        chunk_id  += 1

        print(f'\tChunk {chunk_id} / {-(-num_orders // chunk_size)} done ({id_offset - 1:,} rows)')
    # end while

    print(f'      Orders generated ({num_orders:,} rows)')

    # generates and writes order items in chunks
    print('[4/4] Generating order items...')

    # pre-allocates a fixed-size numpy array for order totals indexed by order_id
    order_totals = np.zeros(num_orders + 1)
    id_offset = 1
    chunk_id = 0
    remaining = num_order_items

    while remaining > 0:
        n = min(chunk_size, remaining)

        chunk = generate_order_items_chunk(chunk_id, n, id_offset, order_ids_np, product_ids, price_lookup, pd, np)

        write_chunk(chunk, path, 'order_items', chunk_id)

        # accumulates line totals per order_id into the pre-allocated array
        np.add.at(order_totals, chunk['order_id'].to_numpy(), (chunk['quantity'] * chunk['unit_price']).to_numpy())
        id_offset += n
        remaining -= n
        chunk_id  += 1

        print(f'\tChunk {chunk_id} / {-(-num_order_items // chunk_size)} done ({id_offset - 1:,} rows)')
    # end while

    print(f'      Order items generated ({num_order_items:,} rows)')

    print('Updating order total_amounts...')

    for csv_file in sorted((path / 'orders').glob('part_*.csv')):
        orders_chunk = pd.read_csv(csv_file)

        orders_chunk['total_amount'] = np.round(order_totals[orders_chunk['order_id'].to_numpy()], 2)
        
        orders_chunk.to_csv(csv_file, index=False)
    # end for-in

    print('Order total_amounts updated.')

    print('\nDone! The dataset has been generated successfully.')
# end def

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce datasets.")

    parser.add_argument("--customers",   type=int,  default=6_000,                      help="Number of customers")
    parser.add_argument("--products",    type=int,  default=2_000,                      help="Number of products")
    parser.add_argument("--orders",      type=int,  default=1_000_000,                  help="Number of orders")
    parser.add_argument("--order-items", type=int,  default=4_000_000,                  help="Number of order items")
    parser.add_argument("--path",        type=Path, default=Path('data/e-commerce'),    help="Output directory")
    parser.add_argument("--chunk-size",  type=int,  default=1_000_000,                  help="Number or rows per chunk")

    args = parser.parse_args()

    main(
        num_customers=      args.customers,
        num_products=       args.products,
        num_orders=         args.orders,
        num_order_items=    args.order_items,
        path=               args.path,
        chunk_size=         args.chunk_size,
    )
# end if