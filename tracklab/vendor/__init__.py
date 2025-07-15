"""Vendor modules for tracklab."""

# Import modules with dashes in their directory names
import sys
import os

# Add vendor paths to sys.path for import compatibility
vendor_dir = os.path.dirname(__file__)

# Add gql vendor module
gql_path = os.path.join(vendor_dir, "gql-0.2.0")
if gql_path not in sys.path:
    sys.path.append(gql_path)

# Add graphql vendor module  
graphql_path = os.path.join(vendor_dir, "graphql-core-1.1")
if graphql_path not in sys.path:
    sys.path.append(graphql_path)

# Add promise vendor module
promise_path = os.path.join(vendor_dir, "promise-2.3.0")
if promise_path not in sys.path:
    sys.path.append(promise_path)

# Add watchdog vendor module
watchdog_path = os.path.join(vendor_dir, "watchdog_0_9_0")
if watchdog_path not in sys.path:
    sys.path.append(watchdog_path)