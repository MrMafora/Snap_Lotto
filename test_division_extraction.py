import logging
import os
import sys
from bs4 import BeautifulSoup
from html_parser import extract_divisions_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML sample resembling the structure in the provided image
sample_html = """
<!DOCTYPE html>
<html>
<head><title>Lottery Results Sample</title></head>
<body>
    <h1>LOTTO RESULTS FOR DRAW ID 2530</h1>
    <div>
        <h2>LOTTO WINNING NUMBERS</h2>
        <div class="ball-container">
            <div class="ball">39</div>
            <div class="ball">42</div>
            <div class="ball">11</div>
            <div class="ball">07</div>
            <div class="ball">37</div>
            <div class="ball">34</div>
            <span>+</span>
            <div class="bonus-ball">44</div>
        </div>
        <div>DRAW DATE: 2025-04-05</div>
        
        <h2>DIVISIONS</h2>
        <table>
            <tr>
                <th>DIVISIONS</th>
                <th>WINNERS</th>
                <th>WINNINGS</th>
            </tr>
            <tr>
                <td>DIV 1</td>
                <td>0</td>
                <td>R0.00</td>
            </tr>
            <tr>
                <td>DIV 2</td>
                <td>1</td>
                <td>R99,273.10</td>
            </tr>
            <tr>
                <td>DIV 3</td>
                <td>38</td>
                <td>R4,543.40</td>
            </tr>
            <tr>
                <td>DIV 4</td>
                <td>96</td>
                <td>R2,248.00</td>
            </tr>
            <tr>
                <td>DIV 5</td>
                <td>2498</td>
                <td>R145.10</td>
            </tr>
            <tr>
                <td>DIV 6</td>
                <td>3042</td>
                <td>R103.60</td>
            </tr>
            <tr>
                <td>DIV 7</td>
                <td>46289</td>
                <td>R50.00</td>
            </tr>
            <tr>
                <td>DIV 8</td>
                <td>33113</td>
                <td>R20.00</td>
            </tr>
        </table>
        
        <h2>MORE INFO</h2>
        <table>
            <tr>
                <td>ROLLOVER AMOUNT</td>
                <td>R8,752,203.22</td>
            </tr>
            <tr>
                <td>ROLLOVER NO</td>
                <td>3</td>
            </tr>
            <tr>
                <td>TOTAL POOL SIZE</td>
                <td>R12,894,254.52</td>
            </tr>
            <tr>
                <td>TOTAL SALES</td>
                <td>R16,206,515.00</td>
            </tr>
            <tr>
                <td>NEXT JACKPOT</td>
                <td>R11,000,000.00</td>
            </tr>
            <tr>
                <td>DRAW MACHINE</td>
                <td>RNG2</td>
            </tr>
            <tr>
                <td>NEXT DRAW DATE</td>
                <td>2025-04-09</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""

# Test the division extraction
def test_division_extraction():
    soup = BeautifulSoup(sample_html, 'html.parser')
    lottery_type = "Lotto"
    
    # Extract divisions data
    divisions_data = extract_divisions_data(soup, sample_html, lottery_type)
    
    # Print the extracted data
    logger.info(f"Extracted divisions data: {divisions_data}")
    
    # Check if we extracted the correct divisions
    expected_divisions = 8
    extracted_divisions = len(divisions_data)
    
    logger.info(f"Expected {expected_divisions} divisions, extracted {extracted_divisions}")
    
    # Check the first division
    if "Division 1" in divisions_data:
        div1 = divisions_data["Division 1"]
        logger.info(f"Division 1 data: {div1}")
        logger.info(f"Winners: {div1.get('winners')}, Prize: {div1.get('prize')}")
    else:
        logger.warning("Division 1 not found in extracted data")
    
    # Log all divisions
    for div_name, div_data in divisions_data.items():
        logger.info(f"{div_name}: Winners: {div_data.get('winners')}, Prize: {div_data.get('prize')}")

if __name__ == "__main__":
    test_division_extraction()