-- SQL script to fix lottery draw IDs with proper foreign key handling
-- This script will properly update or remove duplicate records while maintaining database integrity

-- Begin a transaction so we can roll back if anything goes wrong
BEGIN;

-- 1. First, let's update the imported_record references for draws that need to be deleted
-- We'll identify the lottery_result_id values that need to be remapped

-- For DAILY LOTTERY: Change from 2258 to 2256
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Daily Lottery' AND draw_number = '2256'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Daily Lottery' AND draw_number = '2258'
);

-- For DAILY LOTTERY: Change from 2257 to 2255
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Daily Lottery' AND draw_number = '2255'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Daily Lottery' AND draw_number = '2257'
);

-- For POWERBALL: Change from 1616 to 1615
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Powerball' AND draw_number = '1615'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Powerball' AND draw_number = '1616'
);

-- For POWERBALL PLUS: Change from 1616 to 1615
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Powerball Plus' AND draw_number = '1615'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Powerball Plus' AND draw_number = '1616'
);

-- For LOTTERY: Change from 2642 to 2542
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery' AND draw_number = '2542'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery' AND draw_number = '2642'
);

-- For LOTTERY PLUS 1: Change from 2642 to 2542
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2542'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2642'
);

-- For LOTTERY PLUS 2: Change from 2642 to 2542
UPDATE imported_record
SET lottery_result_id = (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2542'
)
WHERE lottery_result_id IN (
    SELECT id FROM lottery_result 
    WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2642'
);

-- 2. Now delete records with incorrect draw numbers
-- Daily Lottery
DELETE FROM lottery_result WHERE lottery_type = 'Daily Lottery' AND draw_number = '2258';
DELETE FROM lottery_result WHERE lottery_type = 'Daily Lottery' AND draw_number = '2257';

-- Powerball
DELETE FROM lottery_result WHERE lottery_type = 'Powerball' AND draw_number = '1616';

-- Powerball Plus
DELETE FROM lottery_result WHERE lottery_type = 'Powerball Plus' AND draw_number = '1616';

-- Lottery
DELETE FROM lottery_result WHERE lottery_type = 'Lottery' AND draw_number = '2642';

-- Lottery Plus 1
DELETE FROM lottery_result WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2642';

-- Lottery Plus 2
DELETE FROM lottery_result WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2642';

-- 3. Fix any imported_record entries directly with the correct draw numbers
UPDATE imported_record SET draw_number = '2256' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2258';
UPDATE imported_record SET draw_number = '2255' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2257';
UPDATE imported_record SET draw_number = '1615' WHERE lottery_type = 'Powerball' AND draw_number = '1616';
UPDATE imported_record SET draw_number = '1615' WHERE lottery_type = 'Powerball Plus' AND draw_number = '1616';
UPDATE imported_record SET draw_number = '2542' WHERE lottery_type = 'Lottery' AND draw_number = '2642';
UPDATE imported_record SET draw_number = '2542' WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2642';
UPDATE imported_record SET draw_number = '2542' WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2642';

-- Commit the transaction if everything succeeded
COMMIT;