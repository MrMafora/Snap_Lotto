"""
Convert lottery text data to Excel for import
"""
import pandas as pd
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_text_to_excel(text_data, output_path):
    """
    Convert tab-separated text data to Excel format
    
    Args:
        text_data (str): The tab-separated text data 
        output_path (str): Path to save the Excel file
        
    Returns:
        bool: Success status
    """
    # Split the data into lines
    lines = text_data.strip().split('\n')
    
    # Process the text to extract sections for each lottery type
    current_lottery = None
    lottery_data = {}
    headers = None
    
    # Skip the first few lines which are explanatory text
    start_idx = 0
    for idx, line in enumerate(lines):
        if 'Game Name' in line and 'Draw Number' in line and 'Draw Date' in line:
            headers = line.split('\t')
            start_idx = idx
            break
    
    if not headers:
        logger.error("Headers not found in the text data")
        return False
    
    # Process the actual data
    for line in lines[start_idx+1:]:
        if not line.strip():
            continue
            
        # Split by tabs
        fields = line.split('\t')
        
        # Need at least game type, draw number and date to proceed
        if len(fields) < 3:
            continue
            
        # Get the lottery type
        lottery_type = fields[0]
        
        # Skip empty or header-like rows
        if not lottery_type or lottery_type == 'Game Name':
            continue
            
        # If this is a new lottery type, initialize its data structure
        if lottery_type not in lottery_data:
            lottery_data[lottery_type] = []
        
        # Add the row data for this lottery type
        row_data = {}
        for i, header in enumerate(headers):
            if i < len(fields):
                row_data[header] = fields[i]
            else:
                row_data[header] = ""
                
        lottery_data[lottery_type].append(row_data)
    
    # Create Excel writer
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Create a single unified sheet with all lottery types
    all_rows = []
    for lottery_type, rows in lottery_data.items():
        all_rows.extend(rows)
    
    # Create unified dataframe
    df = pd.DataFrame(all_rows)
    
    # Write to Excel - use a single sheet called "Lottery" to match our importer's expectation
    df.to_excel(writer, sheet_name='Lottery', index=False)
    
    # Add timestamp to the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save the Excel file
    writer.close()
    
    logger.info(f"Created Excel file with {sum(len(rows) for rows in lottery_data.values())} rows")
    return os.path.exists(output_path)

# Load the text from your pasted content
text_data = """Okay, I have integrated the data from the latest set of screenshots with all the previously provided information, maintaining the established naming conventions and division descriptions.

Here are the comprehensive, updated spreadsheet tables:

Sheet 1: Lottery Games

(Includes data from all screenshot sets provided, with updated game names and division descriptions)

Game Name	Draw Number	Draw Date	Winning Numbers (Numerical)	Bonus Ball	Div 1 Description	Div 1 Winners	Div 1 Winnings	Div 2 Description	Div 2 Winners	Div 2 Winnings	Div 3 Description	Div 3 Winners	Div 3 Winnings	Div 4 Description	Div 4 Winners	Div 4 Winnings	Div 5 Description	Div 5 Winners	Div 5 Winnings	Div 6 Description	Div 6 Winners	Div 6 Winnings	Div 7 Description	Div 7 Winners	Div 7 Winnings	Div 8 Description	Div 8 Winners	Div 8 Winnings	Rollover Amount	Total Pool Size	Total Sales	Next Jackpot	Draw Machine	Next Draw Date
Lottery	2536	2025-04-26	18 20 28 30 31 36	49	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	46	R6,461.90	Four Correct Numbers + Bonus Ball	111	R2,125.30	Four Correct Numbers	2663	R155.80	Three Correct Numbers + Bonus Ball	3924	R112.50	Three Correct Numbers	44195	R50.00	Two Correct Numbers + Bonus Ball	31455	R20.00	R25,781,422.76	R29,196,096.10	R17,462,875.00	R28,000,000.00	RNG2	2025-04-30
Lottery	2535	2025-04-23	01 05 22 34 44 52	33	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R78,072.60	Five Correct Numbers	36	R5,028.80	Four Correct Numbers + Bonus Ball	119	R1,973.50	Four Correct Numbers	2356	R160.60	Three Correct Numbers + Bonus Ball	34947	R96.90	Three Correct Numbers	46058	R50.00	Two Correct Numbers + Bonus Ball	26844	R20.00	R22,337,141.32	R25,537,974.62	R12,619,320.00	R25,000,000.00	RNG2	2025-04-26
Lottery	2534	2025-04-19	06 09 11 18 51 52	32	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R21,575.20	Five Correct Numbers	30	R4,169.20	Four Correct Numbers + Bonus Ball	96	R2,800.20	Four Correct Numbers	2350	R155.50	Three Correct Numbers + Bonus Ball	3110	R116.10	Three Correct Numbers	41356	R50.00	Two Correct Numbers + Bonus Ball	27101	R20.00	R19,859,182.60	R23,482,110.30	R14,138,150.00	R22,000,000.00	RNG2	2025-04-23
Lottery	2533	2025-04-16	09 16 20 23 26 51	29	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	32	R7,087.80	Four Correct Numbers + Bonus Ball	97	R1,593.00	Four Correct Numbers	1970	R145.70	Three Correct Numbers + Bonus Ball	2870	R91.60	Three Correct Numbers	39216	R50.00	Two Correct Numbers + Bonus Ball	29832	R20.00	R17,120,071.13	R20,645,569.23	R13,474,135.00	R19,000,000.00	RNG2	2025-04-19
Lottery	2532	2025-04-12	03 09 16 17 31 48	16	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	29	R5,764.90	Four Correct Numbers + Bonus Ball	109	R2,018.50	Four Correct Numbers	1817	R152.20	Three Correct Numbers + Bonus Ball	2757	R99.90	Three Correct Numbers	45114	R50.00	Two Correct Numbers + Bonus Ball	32296	R20.00	R14,491,946.40	R18,316,323.60	R15,422,920.00	R16,000,000.00	RNG2	2025-04-16
Lottery	2531	2025-04-09	03 05 27 45 49 50	20	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	30	R7,864.20	Four Correct Numbers + Bonus Ball	70	R2,674.90	Four Correct Numbers	1702	R184.80	Three Correct Numbers + Bonus Ball	2571	R106.30	Three Correct Numbers	34408	R50.00	Two Correct Numbers + Bonus Ball	24154	R20.00	R11,465,905.86	R14,972,497.00	R13,600,440.00	R14,000,000.00	RNG2	2025-04-12
Lottery	2530	2025-04-05	07 11 34 37 39 42	44	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R99,273.10	Five Correct Numbers	38	R4,543.40	Four Correct Numbers + Bonus Ball	96	R2,248.00	Four Correct Numbers	2498	R145.10	Three Correct Numbers + Bonus Ball	3042	R103.60	Three Correct Numbers	46289	R50.00	Two Correct Numbers + Bonus Ball	33113	R20.00	R8,752,203.22	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2529	2025-04-02	06 07 22 29 44 50	04	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2528	2025-03-29	11 18 28 36 46 48	22	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2527	2025-03-26	12 18 21 25 27 38	01	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2526	2025-03-22	03 12 16 18 31 51	02	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2525	2025-03-19	02 03 17 27 29 37	12	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2524	2025-03-15	06 23 24 34 47 49	18	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2523	2025-03-12	07 12 24 32 39 48	09	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2522	2025-03-08	07 19 23 27 31 52	10	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery	2521	2025-03-05	02 03 37 45 48 51	24	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 1	2536	2025-04-26	04 06 21 22 36 43	09	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	36	R4,758.20	Four Correct Numbers + Bonus Ball	95	R2,236.60	Four Correct Numbers	1601	R168.80	Three Correct Numbers + Bonus Ball	2583	R105.00	Three Correct Numbers	40000	R25.00	Two Correct Numbers + Bonus Ball	27583	R15.00	R1,154,793.80	R3,712,614.40	R7,425,202.50	R2,000,000.00	RNG2	2025-04-30
Lottery Plus 1	2535	2025-04-23	03 12 21 30 45 51	31	Six Correct Numbers	1	R13,314,022.70	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	81	R1,514.60	Four Correct Numbers + Bonus Ball	145	R1,801.70	Four Correct Numbers	1976	R154.40	Three Correct Numbers + Bonus Ball	29879	R133.20	Three Correct Numbers	41826	R25.00	Two Correct Numbers + Bonus Ball	21926	R15.00	R0.00	R15,176,012.20	R5,497,055.00	R1,000,000.00	RNG2	2025-04-26
Lottery Plus 1	2534	2025-04-19	10 16 20 24 28 37	12	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	14	R3,435.80	Four Correct Numbers + Bonus Ball	89	R1,128.10	Four Correct Numbers	1430	R136.10	Three Correct Numbers + Bonus Ball	2336	R89.70	Three Correct Numbers	36840	R25.00	Two Correct Numbers + Bonus Ball	31273	R15.00	R12,427,511.57	R14,614,224.77	R6,237,002.50	R14,000,000.00	RNG2	2025-04-23
Lottery Plus 1	2533	2025-04-16	03 04 13 15 28 48	15	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	19	R7,388.80	Four Correct Numbers + Bonus Ball	61	R2,561.90	Four Correct Numbers	1551	R158.90	Three Correct Numbers + Bonus Ball	2498	R105.30	Three Correct Numbers	33663	R25.00	Two Correct Numbers + Bonus Ball	29218	R15.00	R11,495,556.26	R13,557,015.65	R6,022,062.50	R13,000,000.00	RNG2	2025-04-19
Lottery Plus 1	2532	2025-04-12	09 15 20 25 44 46	16	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	18	R4,300.20	Four Correct Numbers + Bonus Ball	95	R1,507.10	Four Correct Numbers	1637	R136.70	Three Correct Numbers + Bonus Ball	2303	R101.50	Three Correct Numbers	40999	R25.00	Two Correct Numbers + Bonus Ball	31303	R15.00	R10,546,211.64	R12,951,183.24	R6,897,315.00	R12,000,000.00	RNG2	2025-04-16
Lottery Plus 1	2531	2025-04-09	01 18 30 40 50 51	49	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R151,916.50	Five Correct Numbers	20	R3,069.10	Four Correct Numbers + Bonus Ball	64	R1,963.50	Four Correct Numbers	1801	R139.60	Three Correct Numbers + Bonus Ball	2226	R113.20	Three Correct Numbers	31248	R25.00	Two Correct Numbers + Bonus Ball	25107	R15.00	R9,552,568.77	R11,516,808.37	R6,025,155.00	R11,000,000.00	RNG2	2025-04-12
Lottery Plus 1	2530	2025-04-05	04 09 18 20 38 39	47	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R170,452.30	Five Correct Numbers	31	R3,665.60	Four Correct Numbers + Bonus Ball	83	R1,698.70	Four Correct Numbers	2248	R125.40	Three Correct Numbers + Bonus Ball	2637	R106.90	Three Correct Numbers	43356	R25.00	Two Correct Numbers + Bonus Ball	28205	R15.00	R8,508,533.89	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 1	2529	2025-04-02	05 16 27 32 36 44	51	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 1	2528	2025-03-29	01 16 18 26 29 36	24	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 1	2527	2025-03-26	01 16 19 24 31 44	51	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 2	2536	2025-04-26	02 07 19 35 40 42	41	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	16	R3,879.10	Four Correct Numbers + Bonus Ball	28	R2,553.40	Four Correct Numbers	1128	R148.50	Three Correct Numbers + Bonus Ball	1903	R105.00	Three Correct Numbers	30289	R25.00	Two Correct Numbers + Bonus Ball	24138	R15.00	R2,056,422.50	R5,037,389.90	R5,306,452.50	R3,000,000.00	RNG2	2025-04-30
Lottery Plus 2	2535	2025-04-23	12 15 17 26 42 43	28	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	22	R3,143.60	Four Correct Numbers + Bonus Ball	65	R1,515.50	Four Correct Numbers	1181	R146.30	Three Correct Numbers + Bonus Ball	1885	R96.40	Three Correct Numbers	31654	R25.00	Two Correct Numbers + Bonus Ball	22993	R15.00	R1,897,489.97	R4,881,422.87	R5,023,462.50	R2,500,000.00	RNG2	2025-04-26
Lottery Plus 2	2534	2025-04-19	01 20 23 28 43 47	49	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	12	R5,599.60	Four Correct Numbers + Bonus Ball	40	R2,156.80	Four Correct Numbers	849	R156.70	Three Correct Numbers + Bonus Ball	1706	R102.30	Three Correct Numbers	25964	R25.00	Two Correct Numbers + Bonus Ball	21307	R15.00	R1,753,556.45	R4,734,989.25	R4,988,842.50	R2,000,000.00	RNG2	2025-04-23
Lottery Plus 2	2533	2025-04-16	08 15 18 20 40 44	07	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	21	R4,002.00	Four Correct Numbers + Bonus Ball	34	R2,136.90	Four Correct Numbers	971	R153.80	Three Correct Numbers + Bonus Ball	1597	R99.00	Three Correct Numbers	27731	R25.00	Two Correct Numbers + Bonus Ball	21798	R15.00	R1,620,123.48	R4,635,989.68	R4,827,882.50	R2,000,000.00	RNG2	2025-04-19
Lottery Plus 2	2532	2025-04-12	04 07 13 17 22 34	47	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	20	R3,714.60	Four Correct Numbers + Bonus Ball	70	R1,554.10	Four Correct Numbers	1058	R133.40	Three Correct Numbers + Bonus Ball	1762	R92.20	Three Correct Numbers	27346	R25.00	Two Correct Numbers + Bonus Ball	22173	R15.00	R1,494,123.48	R4,596,989.68	R4,887,900.00	R2,000,000.00	RNG2	2025-04-16
Lottery Plus 2	2531	2025-04-09	01 06 17 22 40 52	49	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	0	R0.00	Five Correct Numbers	15	R4,619.20	Four Correct Numbers + Bonus Ball	38	R2,156.30	Four Correct Numbers	813	R161.00	Three Correct Numbers + Bonus Ball	1480	R102.40	Three Correct Numbers	23164	R25.00	Two Correct Numbers + Bonus Ball	18971	R15.00	R1,376,123.48	R4,235,989.68	R4,521,850.00	R1,500,000.00	RNG2	2025-04-12
Lottery Plus 2	2530	2025-04-05	04 10 26 35 41 44	08	Six Correct Numbers	0	R0.00	Five Correct Numbers + Bonus Ball	1	R66,842.00	Five Correct Numbers	9	R8,211.70	Four Correct Numbers + Bonus Ball	68	R1,376.50	Four Correct Numbers	882	R153.80	Three Correct Numbers + Bonus Ball	1608	R97.70	Three Correct Numbers	26489	R25.00	Two Correct Numbers + Bonus Ball	21045	R15.00	R1,268,123.48	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 2	2529	2025-04-02	10 18 28 36 41 51	50	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 2	2528	2025-03-29	05 26 38 39 43 47	16	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Lottery Plus 2	2527	2025-03-26	02 07 15 18 42 49	50	Six Correct Numbers	Data N/A	Data N/A	Five Correct Numbers + Bonus Ball	Data N/A	Data N/A	Five Correct Numbers	Data N/A	Data N/A	Four Correct Numbers + Bonus Ball	Data N/A	Data N/A	Four Correct Numbers	Data N/A	Data N/A	Three Correct Numbers + Bonus Ball	Data N/A	Data N/A	Three Correct Numbers	Data N/A	Data N/A	Two Correct Numbers + Bonus Ball	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A	Data N/A
Powerball	1609	2025-04-25	04 23 25 31 32	16	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	21	R11,430.30	3 Correct Numbers + Powerball	60	R4,596.70	3 Correct Numbers	833	R595.70	2 Correct Numbers + Powerball	1308	R271.00	1 Correct Number + Powerball	5893	R131.10	0 Correct Numbers + Powerball	8826	R50.00	R64,407,600.36	R67,432,368.40	R12,341,375.00	R68,000,000.00	RNG2	2025-04-29
Powerball	1608	2025-04-22	13 24 28 33 45	11	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	44	R6,110.30	3 Correct Numbers + Powerball	48	R4,052.50	3 Correct Numbers	1116	R337.00	2 Correct Numbers + Powerball	1236	R178.50	1 Correct Number + Powerball	5996	R87.10	0 Correct Numbers + Powerball	9058	R50.00	R61,419,046.81	R65,010,124.46	R12,984,295.00	R66,000,000.00	RNG2	2025-04-25
Powerball	1607	2025-04-18	07 20 21 23 40	20	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R345,093.40	4 Correct Numbers	35	R7,083.20	3 Correct Numbers + Powerball	107	R2,826.40	3 Correct Numbers	816	R498.20	2 Correct Numbers + Powerball	1652	R215.50	1 Correct Number + Powerball	7370	R100.00	0 Correct Numbers + Powerball	10921	R50.00	R58,432,236.48	R62,461,841.88	R13,592,690.00	R62,000,000.00	RNG2	2025-04-22
Powerball	1606	2025-04-15	02 13 20 22 34	14	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R903,614.70	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	39	R7,770.80	3 Correct Numbers + Powerball	85	R3,275.70	3 Correct Numbers	947	R455.90	2 Correct Numbers + Powerball	1452	R194.40	1 Correct Number + Powerball	6881	R92.10	0 Correct Numbers + Powerball	10302	R50.00	R55,458,892.32	R59,848,736.52	R14,725,930.00	R58,000,000.00	RNG2	2025-04-18
Powerball	1605	2025-04-11	07 09 11 22 44	19	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	45	R7,026.50	3 Correct Numbers + Powerball	106	R2,863.10	3 Correct Numbers	1074	R435.50	2 Correct Numbers + Powerball	1607	R183.50	1 Correct Number + Powerball	7582	R85.40	0 Correct Numbers + Powerball	11396	R50.00	R52,698,263.21	R57,217,984.71	R15,064,057.50	R55,000,000.00	RNG2	2025-04-15
Powerball	1604	2025-04-08	02 10 12 17 37	13	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R795,349.30	4 Correct Numbers + Powerball	1	R201,675.80	4 Correct Numbers	28	R8,345.00	3 Correct Numbers + Powerball	68	R3,562.80	3 Correct Numbers	745	R504.60	2 Correct Numbers + Powerball	1274	R205.00	1 Correct Number + Powerball	5990	R96.20	0 Correct Numbers + Powerball	9101	R50.00	R49,831,252.48	R54,573,651.73	R15,413,995.00	R52,000,000.00	RNG2	2025-04-11
Powerball	1603	2025-04-04	01 15 20 33 38	10	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	52	R5,261.50	3 Correct Numbers + Powerball	101	R2,774.50	3 Correct Numbers	1122	R375.60	2 Correct Numbers + Powerball	1739	R157.20	1 Correct Number + Powerball	8002	R74.60	0 Correct Numbers + Powerball	12210	R50.00	R47,058,743.79	R51,914,822.09	R16,235,275.00	R49,000,000.00	RNG2	2025-04-08
Powerball	1602	2025-04-01	05 06 21 24 45	06	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R1,059,307.70	4 Correct Numbers + Powerball	2	R134,064.70	4 Correct Numbers	25	R7,726.90	3 Correct Numbers + Powerball	103	R2,602.50	3 Correct Numbers	860	R480.70	2 Correct Numbers + Powerball	1499	R197.90	1 Correct Number + Powerball	7192	R89.70	0 Correct Numbers + Powerball	10759	R50.00	R44,369,722.21	R49,329,318.21	R16,532,020.00	R47,000,000.00	RNG2	2025-04-04
Powerball	1601	2025-03-28	01 02 14 29 35	02	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R1,015,764.90	4 Correct Numbers + Powerball	2	R128,587.90	4 Correct Numbers	22	R7,673.30	3 Correct Numbers + Powerball	92	R2,513.40	3 Correct Numbers	866	R422.40	2 Correct Numbers + Powerball	1291	R196.50	1 Correct Number + Powerball	6267	R88.70	0 Correct Numbers + Powerball	8888	R50.00	R41,730,722.21	R46,649,878.21	R16,398,520.00	R45,000,000.00	RNG2	2025-04-01
Powerball	1600	2025-03-25	07 23 28 43 45	16	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	2	R106,682.90	4 Correct Numbers	44	R5,943.50	3 Correct Numbers + Powerball	89	R2,403.10	3 Correct Numbers	984	R338.10	2 Correct Numbers + Powerball	1477	R156.00	1 Correct Number + Powerball	7149	R69.70	0 Correct Numbers + Powerball	10580	R50.00	R39,096,722.21	R44,022,598.21	R16,419,587.50	R42,000,000.00	RNG2	2025-03-28
Powerball	1599	2025-03-21	11 16 17 18 27	06	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	3	R80,642.60	4 Correct Numbers	42	R6,006.10	3 Correct Numbers + Powerball	114	R2,126.10	3 Correct Numbers	971	R393.50	2 Correct Numbers + Powerball	1520	R172.00	1 Correct Number + Powerball	7306	R78.10	0 Correct Numbers + Powerball	10915	R50.00	R36,506,722.21	R41,438,938.21	R16,443,725.00	R39,000,000.00	RNG2	2025-03-25
Powerball	1598	2025-03-18	03 09 12 24 42	15	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R920,375.90	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	33	R7,709.80	3 Correct Numbers + Powerball	85	R2,525.10	3 Correct Numbers	859	R384.10	2 Correct Numbers + Powerball	1369	R176.50	1 Correct Number + Powerball	6680	R78.70	0 Correct Numbers + Powerball	9820	R50.00	R33,916,722.21	R38,850,938.21	R16,454,720.00	R37,000,000.00	RNG2	2025-03-21
Powerball	1597	2025-03-14	04 07 09 22 44	03	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	2	R119,982.20	4 Correct Numbers	37	R5,911.30	3 Correct Numbers + Powerball	89	R2,698.40	3 Correct Numbers	837	R460.70	2 Correct Numbers + Powerball	1395	R178.50	1 Correct Number + Powerball	7002	R76.90	0 Correct Numbers + Powerball	10291	R50.00	R31,343,722.21	R36,275,938.21	R16,443,725.00	R34,000,000.00	RNG2	2025-03-18
Powerball	1596	2025-03-11	07 20 21 30 42	16	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R237,964.40	4 Correct Numbers	31	R6,461.30	3 Correct Numbers + Powerball	58	R3,421.00	3 Correct Numbers	848	R400.00	2 Correct Numbers + Powerball	1077	R186.60	1 Correct Number + Powerball	5340	R82.00	0 Correct Numbers + Powerball	7863	R50.00	R29,043,722.21	R33,882,722.21	R16,119,675.00	R31,000,000.00	RNG2	2025-03-14
Powerball	1595	2025-03-07	06 08 16 37 44	03	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R847,751.10	4 Correct Numbers + Powerball	2	R114,445.90	4 Correct Numbers	34	R5,612.80	3 Correct Numbers + Powerball	95	R2,409.40	3 Correct Numbers	828	R434.60	2 Correct Numbers + Powerball	1452	R169.00	1 Correct Number + Powerball	6956	R77.00	0 Correct Numbers + Powerball	10294	R50.00	R26,843,722.21	R31,776,552.21	R16,440,975.00	R29,000,000.00	RNG2	2025-03-11
Powerball	1594	2025-03-04	01 06 11 13 45	09	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R905,634.20	4 Correct Numbers + Powerball	2	R121,978.10	4 Correct Numbers	34	R5,975.10	3 Correct Numbers + Powerball	94	R2,595.30	3 Correct Numbers	934	R409.00	2 Correct Numbers + Powerball	1490	R170.70	1 Correct Number + Powerball	7203	R76.60	0 Correct Numbers + Powerball	10639	R50.00	R24,643,722.21	R29,576,552.21	R16,443,725.00	R27,000,000.00	RNG2	2025-03-07
Powerball	1593	2025-02-28	01 05 22 32 44	04	5 Correct Numbers + Powerball	1	R23,203,722.21	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	3	R63,996.10	4 Correct Numbers	29	R7,136.20	3 Correct Numbers + Powerball	78	R2,461.40	3 Correct Numbers	862	R363.80	2 Correct Numbers + Powerball	1265	R164.70	1 Correct Number + Powerball	6136	R74.30	0 Correct Numbers + Powerball	9073	R50.00	R1,040,000.00	R26,303,722.21	R15,865,840.00	R3,000,000.00	RNG2	2025-03-04
Powerball Plus	1609	2025-04-25	11 13 35 41 45	19	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	28	R5,135.20	3 Correct Numbers + Powerball	75	R2,290.20	3 Correct Numbers	841	R296.70	2 Correct Numbers + Powerball	1364	R117.10	1 Correct Number + Powerball	6482	R49.30	0 Correct Numbers + Powerball	9758	R20.00	R24,071,217.51	R25,891,877.73	R8,233,950.00	R25,000,000.00	RNG2	2025-04-29
Powerball Plus	1608	2025-04-22	02 04 12 27 40	19	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	30	R5,070.90	3 Correct Numbers + Powerball	76	R2,146.80	3 Correct Numbers	821	R292.80	2 Correct Numbers + Powerball	1317	R114.80	1 Correct Number + Powerball	6223	R48.60	0 Correct Numbers + Powerball	9247	R20.00	R23,211,217.51	R24,911,877.73	R8,215,830.00	R24,000,000.00	RNG2	2025-04-25
Powerball Plus	1607	2025-04-18	14 20 30 34 36	18	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	31	R4,981.70	3 Correct Numbers + Powerball	75	R2,239.70	3 Correct Numbers	823	R297.60	2 Correct Numbers + Powerball	1290	R116.10	1 Correct Number + Powerball	6110	R49.00	0 Correct Numbers + Powerball	9154	R20.00	R22,351,217.51	R24,051,877.73	R8,325,400.00	R23,000,000.00	RNG2	2025-04-22
Powerball Plus	1606	2025-04-15	01 06 16 28 32	04	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	2	R120,025.70	4 Correct Numbers	16	R7,984.00	3 Correct Numbers + Powerball	49	R2,855.90	3 Correct Numbers	814	R292.80	2 Correct Numbers + Powerball	1158	R126.30	1 Correct Number + Powerball	5559	R53.10	0 Correct Numbers + Powerball	8311	R20.00	R21,501,217.51	R23,211,877.73	R8,462,965.00	R23,000,000.00	RNG2	2025-04-18
Powerball Plus	1605	2025-04-11	17 23 24 25 30	20	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	36	R4,584.00	3 Correct Numbers + Powerball	78	R2,122.60	3 Correct Numbers	886	R273.70	2 Correct Numbers + Powerball	1456	R110.10	1 Correct Number + Powerball	7006	R45.70	0 Correct Numbers + Powerball	10516	R20.00	R20,651,217.51	R22,361,877.73	R8,566,800.00	R22,000,000.00	RNG2	2025-04-15
Powerball Plus	1604	2025-04-08	07 19 31 32 35	20	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R431,717.50	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	27	R6,426.20	3 Correct Numbers + Powerball	88	R1,964.20	3 Correct Numbers	800	R316.30	2 Correct Numbers + Powerball	1409	R110.40	1 Correct Number + Powerball	6800	R45.80	0 Correct Numbers + Powerball	10221	R20.00	R19,801,217.51	R21,511,877.73	R8,516,300.00	R21,000,000.00	RNG2	2025-04-11
Powerball Plus	1603	2025-04-04	05 10 18 28 43	15	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R188,462.60	4 Correct Numbers	23	R6,526.90	3 Correct Numbers + Powerball	84	R2,243.60	3 Correct Numbers	786	R351.60	2 Correct Numbers + Powerball	1329	R121.90	1 Correct Number + Powerball	6368	R50.70	0 Correct Numbers + Powerball	9507	R20.00	R18,951,217.51	R20,661,877.73	R8,556,300.00	R20,000,000.00	RNG2	2025-04-08
Powerball Plus	1602	2025-04-01	09 17 19 24 39	12	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	4	R51,591.80	4 Correct Numbers	28	R6,177.70	3 Correct Numbers + Powerball	64	R2,242.90	3 Correct Numbers	792	R267.60	2 Correct Numbers + Powerball	1175	R117.60	1 Correct Number + Powerball	5614	R49.30	0 Correct Numbers + Powerball	8405	R20.00	R18,101,217.51	R19,811,877.73	R8,505,300.00	R19,000,000.00	RNG2	2025-04-04
Powerball Plus	1601	2025-03-28	03 09 11 28 30	13	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	19	R7,962.40	3 Correct Numbers + Powerball	80	R2,130.50	3 Correct Numbers	783	R320.20	2 Correct Numbers + Powerball	1259	R121.40	1 Correct Number + Powerball	6038	R50.60	0 Correct Numbers + Powerball	9062	R20.00	R17,251,217.51	R18,961,877.73	R8,555,300.00	R18,000,000.00	RNG2	2025-04-01
Powerball Plus	1600	2025-03-25	05 21 29 34 37	10	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	27	R6,164.10	3 Correct Numbers + Powerball	77	R2,156.50	3 Correct Numbers	787	R310.30	2 Correct Numbers + Powerball	1229	R115.60	1 Correct Number + Powerball	5894	R48.10	0 Correct Numbers + Powerball	8824	R20.00	R16,401,217.51	R18,111,877.73	R8,553,300.00	R17,000,000.00	RNG2	2025-03-28
Powerball Plus	1599	2025-03-21	04 09 18 33 45	05	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R180,661.60	4 Correct Numbers	24	R6,383.60	3 Correct Numbers + Powerball	63	R2,147.20	3 Correct Numbers	736	R269.70	2 Correct Numbers + Powerball	1146	R119.20	1 Correct Number + Powerball	5557	R49.30	0 Correct Numbers + Powerball	8322	R20.00	R15,551,217.51	R17,261,877.73	R8,554,300.00	R16,000,000.00	RNG2	2025-03-25
Powerball Plus	1598	2025-03-18	05 11 19 22 33	08	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R430,661.60	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	21	R6,884.60	3 Correct Numbers + Powerball	78	R2,173.90	3 Correct Numbers	797	R313.10	2 Correct Numbers + Powerball	1274	R118.30	1 Correct Number + Powerball	6146	R49.00	0 Correct Numbers + Powerball	9201	R20.00	R14,701,217.51	R16,411,877.73	R8,553,300.00	R16,000,000.00	RNG2	2025-03-21
Powerball Plus	1597	2025-03-14	13 16 19 33 36	19	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R171,877.73	4 Correct Numbers	33	R5,208.40	3 Correct Numbers + Powerball	70	R2,230.30	3 Correct Numbers	832	R275.30	2 Correct Numbers + Powerball	1232	R117.20	1 Correct Number + Powerball	5944	R48.60	0 Correct Numbers + Powerball	8901	R20.00	R13,851,217.51	R15,561,877.73	R8,555,300.00	R15,000,000.00	RNG2	2025-03-18
Powerball Plus	1596	2025-03-11	05 26 35 40 45	19	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	0	R0.00	4 Correct Numbers	24	R6,989.90	3 Correct Numbers + Powerball	72	R2,332.00	3 Correct Numbers	784	R314.30	2 Correct Numbers + Powerball	1220	R120.60	1 Correct Number + Powerball	5880	R50.10	0 Correct Numbers + Powerball	8787	R20.00	R13,001,217.51	R14,711,877.73	R8,555,300.00	R14,000,000.00	RNG2	2025-03-14
Powerball Plus	1595	2025-03-07	10 17 18 20 42	01	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R163,877.73	4 Correct Numbers	37	R5,254.10	3 Correct Numbers + Powerball	75	R2,185.00	3 Correct Numbers	880	R273.50	2 Correct Numbers + Powerball	1243	R115.10	1 Correct Number + Powerball	5999	R47.80	0 Correct Numbers + Powerball	9006	R20.00	R12,151,217.51	R13,861,877.73	R8,553,300.00	R13,000,000.00	RNG2	2025-03-11
Powerball Plus	1594	2025-03-04	05 10 30 35 44	08	5 Correct Numbers + Powerball	0	R0.00	5 Correct Numbers	1	R363,106.50	4 Correct Numbers + Powerball	1	R156,877.70	4 Correct Numbers	27	R7,271.20	3 Correct Numbers + Powerball	78	R2,007.40	3 Correct Numbers	886	R258.60	2 Correct Numbers + Powerball	1255	R111.30	1 Correct Number + Powerball	6064	R46.00	0 Correct Numbers + Powerball	9087	R20.00	R11,301,217.51	R13,011,877.73	R8,553,300.00	R12,000,000.00	RNG2	2025-03-07
Powerball Plus	1593	2025-02-28	12 16 23 31 38	06	5 Correct Numbers + Powerball	1	R10,451,217.51	5 Correct Numbers	0	R0.00	4 Correct Numbers + Powerball	1	R149,577.70	4 Correct Numbers	38	R5,243.20	3 Correct Numbers + Powerball	80	R1,909.90	3 Correct Numbers	941	R238.70	2 Correct Numbers + Powerball	1300	R104.60	1 Correct Number + Powerball	6265	R43.40	0 Correct Numbers + Powerball	9390	R20.00	R850,000.00	R12,011,877.73	R8,553,300.00	R1,000,000.00	RNG2	2025-03-04
Daily Lottery	2236	2025-04-26	05 11 23 28 30		Five Correct Numbers	1	R361,750.30	Four Correct Numbers	62	R1,026.00	Three Correct Numbers	2106	R50.10	Two Correct Numbers	23053	R5.00	Zero Correct Numbers	12493	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R0.00	R1,216,402.35	R2,432,778.00	R0.00	RNG2	2025-04-27
Daily Lottery	2235	2025-04-25	02 11 14 17 27		Five Correct Numbers	1	R347,422.10	Four Correct Numbers	51	R1,110.20	Three Correct Numbers	1764	R50.70	Two Correct Numbers	18922	R5.00	Zero Correct Numbers	10231	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R0.00	R1,123,423.10	R2,246,820.50	R0.00	RNG2	2025-04-26
Daily Lottery	2234	2025-04-24	06 11 17 18 24		Five Correct Numbers	0	R0.00	Four Correct Numbers	109	R597.80	Three Correct Numbers	2308	R47.10	Two Correct Numbers	23401	R5.00	Zero Correct Numbers	12662	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R326,422.10	R1,072,778.30	R2,145,530.70	R0.00	RNG2	2025-04-25
Daily Lottery	2233	2025-04-23	05 12 21 29 35		Five Correct Numbers	1	R269,675.90	Four Correct Numbers	82	R697.60	Three Correct Numbers	1935	R49.00	Two Correct Numbers	20177	R5.00	Zero Correct Numbers	10918	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R0.00	R961,243.45	R1,922,461.00	R0.00	RNG2	2025-04-24
Daily Lottery	2232	2025-04-22	10 11 18 25 34		Five Correct Numbers	0	R0.00	Four Correct Numbers	59	R1,006.40	Three Correct Numbers	1922	R51.70	Two Correct Numbers	20511	R5.00	Zero Correct Numbers	11100	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R224,675.90	R931,675.90	R1,863,326.00	R0.00	RNG2	2025-04-23
Daily Lottery	2231	2025-04-21	02 06 08 28 31		Five Correct Numbers	2	R110,337.90	Four Correct Numbers	66	R845.20	Three Correct Numbers	2160	R43.00	Two Correct Numbers	22751	R5.00	Zero Correct Numbers	12313	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R0.00	R879,675.90	R1,759,326.00	R0.00	RNG2	2025-04-22
Daily Lottery	2230	2025-04-20	07 10 19 24 36		Five Correct Numbers	1	R182,675.90	Four Correct Numbers	73	R783.60	Three Correct Numbers	2001	R44.20	Two Correct Numbers	21064	R5.00	Zero Correct Numbers	11398	R2.50	0	0	R0.00	0	0	R0.00	0	0	R0.00	R0.00	R724,675.90	R1,449,326.00	R0.00	RNG2	2025-04-21
"""

output_path = 'attached_assets/lottery_data_template_converted.xlsx'
convert_text_to_excel(text_data, output_path)

print(f"Successfully created Excel file at {output_path}")