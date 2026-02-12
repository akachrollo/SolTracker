import duckdb
import pandas as pd

# Create a tiny table in memory
data = {'Coin': ['SOL', 'JUP', 'BONK'], 'Price': [100, 1.2, 0.00002]}
df = pd.DataFrame(data)

# Use DuckDB to "query" it
result = duckdb.query("SELECT * FROM df WHERE Price > 1").to_df()

print("--- Your Data Engine is Working! ---")
print(result)