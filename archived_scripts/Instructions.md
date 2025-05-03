
# Lottery Application Winning Logic Analysis

## Files and Functions Related to Winning Logic

1. **ticket_scanner.py**
- Main function: `process_ticket_image()`
- Critical function: `get_prize_info()`
- Purpose: Handles ticket scanning and prize determination

2. **data_aggregator.py**
- Function: `validate_and_correct_known_draws()`
- Purpose: Validates lottery results against known correct data

## Current Logic Analysis

### Prize Determination Process
1. The `process_ticket_image()` function in ticket_scanner.py:
   - Extracts numbers from ticket images
   - Compares against winning numbers
   - Calls `get_prize_info()` to determine prizes

2. Prize calculation in `get_prize_info()`:
   - Checks matched numbers
   - Validates bonus number matches
   - Uses division structure for prize determination

### Identified Issues

1. **Division Logic Gaps**
- The division matching logic in `get_prize_info()` may not handle all prize tiers correctly
- Missing validation for specific game types like Powerball Plus

2. **Bonus Number Handling**
- Current logic may not properly account for bonus numbers in prize calculations
- Some game types have different bonus number rules

3. **Prize Validation**
- Missing comprehensive validation against known winning combinations
- Limited error handling for edge cases

4. **Game Type Specific Rules**
- Not all game types follow the same winning patterns
- Need separate validation logic for each game type

## Action Plan

### 1. Enhance Prize Logic
```python
def get_prize_info(lottery_type, matched_numbers, matched_bonus, lottery_result):
    # Add game-specific validation
    if "Powerball" in lottery_type:
        return validate_powerball_prize(matched_numbers, matched_bonus)
    elif "Lotto" in lottery_type:
        return validate_lotto_prize(matched_numbers, matched_bonus)
    # Add other game types...
```

### 2. Fix Bonus Number Handling
- Implement proper bonus number validation for each game type
- Add specific checks for Powerball vs Lotto bonus rules

### 3. Improve Prize Validation
- Expand the KNOWN_CORRECT_DRAWS dictionary in data_aggregator.py
- Add more test cases for each game type

### 4. Add Game-Specific Rules
- Create separate validation functions for each game type
- Implement proper division structure for each game

## Implementation Steps

1. Update ticket_scanner.py:
   - Enhance prize determination logic
   - Add game-specific validation functions
   - Improve error handling

2. Modify data_aggregator.py:
   - Add more known correct draws
   - Enhance validation functions

3. Add test cases:
   - Create comprehensive test suite
   - Test each game type separately
   - Validate edge cases

4. Documentation:
   - Update code comments
   - Document game-specific rules
   - Add validation criteria

## Testing Plan

1. Unit Tests:
   - Test each prize determination function
   - Validate bonus number handling
   - Check division calculations

2. Integration Tests:
   - Test complete ticket scanning process
   - Validate prize calculations
   - Test known winning tickets

3. Edge Cases:
   - Multiple matches in single ticket
   - Invalid number combinations
   - Missing bonus numbers

## Recommendations

1. Create separate modules for each game type's logic
2. Implement comprehensive logging for debugging
3. Add validation checks at each step
4. Create test suite with known winning combinations
5. Document all game rules and prize structures

## Next Steps

1. Implement game-specific validation functions
2. Update prize determination logic
3. Add comprehensive test cases
4. Enhance error handling
5. Update documentation

This should provide a structured approach to fixing the lottery winning logic while maintaining proper validation and error handling.
