# Lottery Data Integrity Rules

## Critical Business Rules for Draw ID Assignments

### Overview

The South African National Lottery offers multiple games that are drawn together on the same day. This document outlines the critical business rules for maintaining data integrity in our lottery database, particularly regarding draw ID assignments.

### Relationship Between Lottery Games

The following lottery games are drawn together and MUST always share the same draw ID:

1. **Lottery Group**:
   - **Lottery** (primary)
   - **Lottery Plus 1**
   - **Lottery Plus 2**

2. **Powerball Group**:
   - **Powerball** (primary)
   - **Powerball Plus**

3. **Daily Lottery** is a standalone game and not grouped with other games.

### Business Rules

1. **Same Draw ID Rule**: 
   - When games are drawn together (e.g., Lottery, Lottery Plus 1, and Lottery Plus 2), they MUST share the same draw ID.
   - It is impossible to have a new draw ID for Lottery without corresponding new data for Lottery Plus 1 and Lottery Plus 2.
   - Similarly, Powerball and Powerball Plus must share the same draw ID.

2. **Primary Game Definition**:
   - The primary game in each group (Lottery for the Lottery group, Powerball for the Powerball group) serves as the source of truth for draw IDs.
   - If there's a discrepancy in draw IDs, the primary game's draw ID should be used for all games in that group.

3. **Data Completeness**:
   - For every draw of a primary game, corresponding draw data for all related games must be present in the database.
   - Missing data for related games indicates a data integrity issue that should be addressed.

### Enforcement Mechanisms

The following mechanisms are in place to enforce these rules:

1. **Import Process**:
   - The `integrity_import.py` script ensures that games drawn together are assigned the same draw ID during data import.
   - When importing data, the script checks for existing records and ensures consistent draw IDs.

2. **Data Integrity Checking**:
   - The `fix_lottery_relationships.py` utility identifies and corrects inconsistencies in existing data.
   - Regular integrity checks should be scheduled to maintain data quality.

3. **Database Constraints**:
   - The primary keys of the `lottery_result` table include `lottery_type` and `draw_number` to prevent duplicate entries.
   - Additional application-level validation ensures consistency between related game draws.

### Data Validation

To validate data integrity:

1. Run the integrity check utility:
   ```bash
   python fix_lottery_relationships.py
   ```

2. Fix identified issues:
   ```bash
   python fix_lottery_relationships.py --fix
   ```

3. Import new data with integrity enforcement:
   ```bash
   python integrity_import.py latest_lottery_data.txt
   ```

### Example of Correct Data

| Lottery Type    | Draw Number | Draw Date   |
|-----------------|-------------|-------------|
| Lottery         | 2538        | 2025-05-03  |
| Lottery Plus 1  | 2538        | 2025-05-03  |
| Lottery Plus 2  | 2538        | 2025-05-03  |
| Powerball       | 1610        | 2025-05-02  |
| Powerball Plus  | 1610        | 2025-05-02  |
| Daily Lottery   | 2239        | 2025-05-02  |

### Example of Incorrect Data (Violation of Draw ID Consistency)

| Lottery Type    | Draw Number | Draw Date   |
|-----------------|-------------|-------------|
| Lottery         | 2538        | 2025-05-03  |
| Lottery Plus 1  | 2537        | 2025-05-03  | <!-- INCORRECT: Should be 2538 -->
| Lottery Plus 2  | 2536        | 2025-05-03  | <!-- INCORRECT: Should be 2538 -->

### Impact of Inconsistent Draw IDs

Inconsistent draw IDs can lead to:

1. Inaccurate analytics and reporting
2. Confusion for users checking results
3. Difficulty in tracking related draws
4. Challenges in data reconciliation and verification
5. Issues with data export and integration with other systems

### Implementation Notes for Developers

When implementing new features that interact with lottery data:

1. Always use the provided `integrity_import.py` script for importing new data.
2. If creating new import processes, enforce the same-draw-ID rule for related games.
3. Run integrity checks after large data imports or migrations.
4. Never manually assign draw IDs that could break the relationship between games.
5. When querying data, be aware that related games share draw IDs and can be joined on this basis.

By following these guidelines, we maintain the integrity of our lottery data system and ensure accurate reporting and analysis.