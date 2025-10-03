-- =====================================================
-- SNAP LOTTO PRODUCTION DATABASE SEED
-- Generated: October 2025
-- =====================================================

-- Lottery Results (Most Recent)
-- =====================================================

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2393, '2025-10-02', '[10, 11, 14, 26, 34]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2392, '2025-10-01', '[1, 20, 24, 26, 27]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2581, '2025-10-01', '[5, 12, 14, 20, 28, 30]', '[16]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2581, '2025-10-01', '[10, 15, 17, 27, 45, 48]', '[3]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2581, '2025-10-01', '[3, 5, 14, 38, 48, 49]', '[27]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2391, '2025-09-30', '[11, 22, 26, 28, 34]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1655, '2025-09-30', '[14, 22, 25, 37, 46]', '[4]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL PLUS', 1655, '2025-09-30', '[1, 10, 23, 25, 44]', '[13]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2390, '2025-09-29', '[4, 11, 20, 25, 31]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2389, '2025-09-28', '[6, 13, 22, 23, 26]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2388, '2025-09-27', '[2, 16, 17, 21, 30]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2580, '2025-09-27', '[7, 12, 14, 32, 37, 52]', '[5]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2580, '2025-09-27', '[2, 12, 15, 27, 34, 40]', '[53]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2580, '2025-09-27', '[3, 4, 9, 19, 38, 58]', '[43]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2387, '2025-09-26', '[12, 17, 28, 29, 36]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1654, '2025-09-26', '[3, 13, 19, 24, 40]', '[12]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL PLUS', 1654, '2025-09-26', '[7, 14, 40, 41, 45]', '[7]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2386, '2025-09-25', '[7, 9, 16, 22, 34]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2385, '2025-09-24', '[10, 18, 28, 31, 32]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2579, '2025-09-24', '[16, 23, 32, 42, 49, 58]', '[55]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2579, '2025-09-24', '[4, 14, 18, 20, 27, 55]', '[40]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2579, '2025-09-24', '[5, 32, 48, 51, 52, 54]', '[9]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2384, '2025-09-23', '[14, 15, 16, 31, 35]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1653, '2025-09-23', '[10, 23, 32, 43, 45]', '[18]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL PLUS', 1653, '2025-09-23', '[10, 14, 25, 42, 50]', '[18]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2383, '2025-09-22', '[2, 5, 6, 11, 25]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2382, '2025-09-21', '[2, 11, 14, 21, 26]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2381, '2025-09-20', '[1, 3, 8, 16, 27]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2578, '2025-09-20', '[4, 5, 14, 21, 34, 52]', '[46]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2578, '2025-09-20', '[13, 21, 33, 40, 45, 50]', '[12]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2578, '2025-09-20', '[20, 27, 31, 32, 38, 42]', '[36]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2380, '2025-09-19', '[9, 16, 20, 26, 35]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1652, '2025-09-19', '[2, 16, 24, 41, 47]', '[19]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL PLUS', 1652, '2025-09-19', '[4, 18, 34, 42, 50]', '[13]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2379, '2025-09-18', '[3, 11, 13, 25, 32]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2378, '2025-09-17', '[5, 25, 27, 29, 33]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2577, '2025-09-17', '[12, 18, 23, 27, 38, 52]', '[48]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2577, '2025-09-17', '[17, 20, 21, 29, 39, 43]', '[47]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2577, '2025-09-17', '[4, 10, 16, 21, 32, 33]', '[49]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2377, '2025-09-16', '[4, 12, 14, 18, 26]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1651, '2025-09-16', '[22, 24, 26, 33, 35]', '[7]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL PLUS', 1651, '2025-09-16', '[5, 13, 15, 30, 39]', '[13]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2376, '2025-09-15', '[5, 11, 15, 16, 25]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2375, '2025-09-14', '[3, 11, 28, 29, 35]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2374, '2025-09-13', '[7, 9, 20, 26, 30]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO', 2576, '2025-09-13', '[12, 20, 21, 22, 28, 33]', '[42]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 1', 2576, '2025-09-13', '[8, 28, 35, 40, 42, 48]', '[50]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('LOTTO PLUS 2', 2576, '2025-09-13', '[1, 9, 14, 17, 37, 42]', '[34]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('DAILY LOTTO', 2373, '2025-09-12', '[7, 10, 28, 30, 34]', NULL)
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;

INSERT INTO lottery_results (lottery_type, draw_number, draw_date, main_numbers, bonus_numbers)
VALUES ('POWERBALL', 1650, '2025-09-12', '[17, 23, 25, 26, 37]', '[18]')
ON CONFLICT (lottery_type, draw_number) DO UPDATE SET main_numbers = EXCLUDED.main_numbers;


-- AI Predictions (Active)
-- =====================================================

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('DAILY LOTTO', '[8, 15, 17, 26, 35]', NULL, 3.5, 'AI Neural Network', 'Auto-generated by PredictionOrchestrator', '2025-10-03', NULL, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO', '[12, 14, 20, 28, 37, 52]', NULL, 3.6, 'Phase 2 Neural Network Ensemble (Random Forest + Gradient Boosting + Neural Network)', 'Advanced ML feature scoring (31 draws analyzed) | Temporal decay weighting + momentum analysis | 6 hot numbers selected | 3.6% confidence from feature ensemble', '2025-10-04', 2582, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO', '[3, 10, 15, 24, 36, 48]', '[8]', 3.2, 'AI Neural Network', 'Auto-generated by PredictionOrchestrator', '2025-10-04', NULL, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO PLUS 1', '[13, 19, 21, 27, 36, 43]', NULL, 3.0, 'Fresh Draw-Specific Prediction Engine', 'Phase 1 frequency analysis using 26 historical draws | Selected 3 hot numbers | Selected 1 cold numbers | Confidence based on frequency patterns and statistical analysis', '2025-10-04', 2582, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO PLUS 1', '[9, 21, 30, 31, 47, 50]', '[52]', 3.4, 'AI Neural Network', 'Auto-generated by PredictionOrchestrator', '2025-10-04', NULL, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO PLUS 2', '[7, 8, 9, 28, 48, 51]', NULL, 3.0, 'Fresh Draw-Specific Prediction Engine', 'Phase 1 frequency analysis using 26 historical draws | Selected 3 hot numbers | Selected 1 cold numbers | Confidence based on frequency patterns and statistical analysis', '2025-10-04', 2582, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('LOTTO PLUS 2', '[16, 20, 24, 28, 43, 51]', '[1]', 3.1, 'AI Neural Network', 'Auto-generated by PredictionOrchestrator', '2025-10-04', NULL, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('POWERBALL', '[19, 26, 37, 41, 47]', '[19]', 2.8, 'Fresh Draw-Specific Prediction Engine', 'Phase 1 frequency analysis using 27 historical draws | Selected 2 hot numbers | Selected 1 cold numbers | Confidence based on frequency patterns and statistical analysis', '2025-10-03', 1656, 'pending', false);

INSERT INTO lottery_predictions (game_type, predicted_numbers, bonus_numbers, confidence_score, prediction_method, reasoning, target_draw_date, linked_draw_id, validation_status, is_verified)
VALUES ('POWERBALL PLUS', '[9, 14, 31, 33, 39]', '[17]', 2.8, 'Fresh Draw-Specific Prediction Engine', 'Phase 1 frequency analysis using 26 historical draws | Selected 2 hot numbers | Selected 1 cold numbers | Confidence based on frequency patterns and statistical analysis', '2025-10-03', 1656, 'pending', false);

