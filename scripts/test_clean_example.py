#!/usr/bin/env python3
"""
Test file for clean_commented_code.py script.
This docstring should be preserved.
"""

# This is a regular comment that should be preserved
import os
import sys


class TestClass:
    """This docstring should be preserved."""
    
    def __init__(self):
        self.value = 42
        # This inline comment should be preserved
        
        
    def new_method(self):
        # Regular comment should be preserved
        return "new"




# This is just a comment about the weather
# Weather is nice today

def active_function():
    """Active function docstring."""
    # This comment should be preserved
    return True


# Final comment about the code