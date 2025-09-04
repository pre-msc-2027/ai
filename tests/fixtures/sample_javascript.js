/**
 * Sample JavaScript file with various code issues for testing
 */

const express = require('express');
const unused = require('unused-package'); // Line 6: Unused import

function calculateTotal(items) {
    console.log('Calculating total...'); // Line 9: Should use proper logger
    let total = 0;

    for (let item of items) {
        total = total + item.price; // Could use += operator
    }

    return total;
}

class ShoppingCart {
    constructor() {
        this.items = [];
        this.apiKey = 'sk_live_1234567890abcdef'; // Line 22: Hardcoded API key
    }

    addItem(item) {
        console.log(`Adding item: ${item.name}`); // Line 26: Console.log
        // This is an extremely long line that goes way beyond 120 characters and should definitely be split into multiple lines for better code readability
        this.items.push(item);
    }

    checkout() {
        try {
            const total = calculateTotal(this.items);
            console.log(`Total: $${total}`); // Line 34: Console.log
            return total;
        } catch (error) {
            // TODO: Implement proper error handling // Line 37: TODO comment
        }
    }

    removeItem(itemId) {
        // FIXME: This doesn't actually remove the item // Line 42: FIXME comment
        console.log(`Removing item: ${itemId}`); // Line 43: Console.log
    }
}

function unusedHelper() { // Line 47: Unused function
    return 'This is never used';
}

module.exports = {
    ShoppingCart,
    calculateTotal
};
