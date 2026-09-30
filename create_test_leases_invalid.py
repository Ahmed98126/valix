import pandas as pd
from datetime import datetime

# Create a lease that ends before the invoice period
data = {
    'unit_id': ['UNIT001'],
    'tenant_name': ['Test Tenant'],
    'lease_start': ['2013-01-01'],  # Lease starts before invoice period
    'lease_end': ['2013-12-31']     # Lease ends before invoice period (08/01/2014)
}

df = pd.DataFrame(data)
df.to_excel('test_leases_invalid.xlsx', index=False)
print('Created test_leases_invalid.xlsx')