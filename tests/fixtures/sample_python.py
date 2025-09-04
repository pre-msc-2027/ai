#!/usr/bin/env python3
"""
Sample Python file with various code issues for testing
"""

import json
import os
import sys

import unused_module  # Line 9: Unused import


def calculate_sum(numbers):
    """Calculate sum of numbers"""
    print("Calculating sum...")  # Line 13: Should use logger
    total = 0
    for num in numbers:
        total = total + num  # Could use += operator
    return total


def process_data(data):
    # TODO: Implement data validation  # Line 20: TODO comment
    result = []
    for item in data:
        if item > 10:
            print(f"Processing item: {item}")  # Line 24: Should use logger
            result.append(item * 2)
    return result


class DataProcessor:
    def __init__(self):
        self.api_key = "hardcoded_secret_key_123"  # Line 30: Hardcoded credential
        self.data = []

    def add_data(self, item):
        # This is a very long line that definitely exceeds 120 characters
        # and should be split for better readability according to style guidelines
        self.data.append(item)

    def process(self):
        try:
            process_data(self.data)
        except Exception:  # Line 39: Empty catch block
            pass
        return []


def unused_function():  # Line 43: Unused function
    """This function is never called"""
    x = 10
    y = 20
    z = x + y
    return z


if __name__ == "__main__":
    processor = DataProcessor()
    processor.add_data(15)
    processor.add_data(25)
    results = processor.process()
    print(results)  # Line 56: Should use logger
