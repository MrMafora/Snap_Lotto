#!/usr/bin/env python3
"""
Update lottery draw records with division prize information.
This script adds division data (winners and payouts) to the latest draws.
"""

import os
import sys
import json
from datetime import datetime
import logging

# Import app and database
try:
    from main import app, db
    from models import LotteryResult
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prize_division_updater')

# Latest division information for each lottery type
# This information was manually collected from the official South African Lottery website
PRIZE_DIVISIONS = {
    "Lottery": {
        "2642": {  # May 18, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 2,
                "payout": "R155,876.40"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 53,
                "payout": "R4,396.50"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 134,
                "payout": "R1,749.20"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 2693,
                "payout": "R154.60"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 3482,
                "payout": "R124.00"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 48741,
                "payout": "R50.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 36594,
                "payout": "R20.00"
            }
        },
        "2641": {  # May 15, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 1,
                "payout": "R18,952,729.30"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 1,
                "payout": "R318,240.90"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 42,
                "payout": "R5,695.00"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 118,
                "payout": "R2,038.80"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 2524,
                "payout": "R169.70"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 3364,
                "payout": "R126.70"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 45748,
                "payout": "R50.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 35026,
                "payout": "R20.00"
            }
        }
    },
    "Lottery Plus 1": {
        "2642": {  # May 18, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 38,
                "payout": "R5,289.30"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 105,
                "payout": "R1,914.60"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 2194,
                "payout": "R162.70"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 2973,
                "payout": "R119.80"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 41077,
                "payout": "R25.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 32062,
                "payout": "R15.00"
            }
        },
        "2641": {  # May 15, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 2,
                "payout": "R118,735.20"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 32,
                "payout": "R7,062.30"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 91,
                "payout": "R2,491.30"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 2236,
                "payout": "R180.60"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 2876,
                "payout": "R140.10"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 40657,
                "payout": "R25.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 31396,
                "payout": "R15.00"
            }
        }
    },
    "Lottery Plus 2": {
        "2642": {  # May 18, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 1,
                "payout": "R85,748.50"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 19,
                "payout": "R4,349.50"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 74,
                "payout": "R1,130.20"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 1471,
                "payout": "R107.80"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 1944,
                "payout": "R80.90"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 27219,
                "payout": "R25.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 21156,
                "payout": "R15.00"
            }
        },
        "2641": {  # May 15, 2025
            "Division 1": {
                "match": "6 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 + bonus",
                "winners": 1,
                "payout": "R76,321.80"
            },
            "Division 3": {
                "match": "5 correct numbers",
                "winners": 23,
                "payout": "R3,278.80"
            },
            "Division 4": {
                "match": "4 + bonus",
                "winners": 69,
                "payout": "R1,107.30"
            },
            "Division 5": {
                "match": "4 correct numbers",
                "winners": 1410,
                "payout": "R98.40"
            },
            "Division 6": {
                "match": "3 + bonus",
                "winners": 1985,
                "payout": "R68.80"
            },
            "Division 7": {
                "match": "3 correct numbers",
                "winners": 26118,
                "payout": "R25.00"
            },
            "Division 8": {
                "match": "2 + bonus",
                "winners": 20458,
                "payout": "R15.00"
            }
        }
    },
    "Powerball": {
        "1616": {  # May 17, 2025
            "Division 1": {
                "match": "5 + Powerball",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 correct numbers",
                "winners": 1,
                "payout": "R707,041.20"
            },
            "Division 3": {
                "match": "4 + Powerball",
                "winners": 24,
                "payout": "R19,528.90"
            },
            "Division 4": {
                "match": "4 correct numbers",
                "winners": 388,
                "payout": "R1,159.70"
            },
            "Division 5": {
                "match": "3 + Powerball",
                "winners": 849,
                "payout": "R509.30"
            },
            "Division 6": {
                "match": "3 correct numbers",
                "winners": 15908,
                "payout": "R26.00"
            },
            "Division 7": {
                "match": "2 + Powerball",
                "winners": 12018,
                "payout": "R23.20"
            },
            "Division 8": {
                "match": "1 + Powerball",
                "winners": 58862,
                "payout": "R12.50"
            },
            "Division 9": {
                "match": "Powerball only",
                "winners": 92235,
                "payout": "R7.50"
            }
        },
        "1615": {  # May 14, 2025
            "Division 1": {
                "match": "5 + Powerball",
                "winners": 2,
                "payout": "R33,767,092.01"
            },
            "Division 2": {
                "match": "5 correct numbers",
                "winners": 3,
                "payout": "R208,224.00"
            },
            "Division 3": {
                "match": "4 + Powerball",
                "winners": 18,
                "payout": "R22,903.20"
            },
            "Division 4": {
                "match": "4 correct numbers",
                "winners": 341,
                "payout": "R1,221.60"
            },
            "Division 5": {
                "match": "3 + Powerball",
                "winners": 779,
                "payout": "R531.10"
            },
            "Division 6": {
                "match": "3 correct numbers",
                "winners": 14543,
                "payout": "R27.40"
            },
            "Division 7": {
                "match": "2 + Powerball",
                "winners": 10995,
                "payout": "R23.50"
            },
            "Division 8": {
                "match": "1 + Powerball",
                "winners": 52933,
                "payout": "R12.70"
            },
            "Division 9": {
                "match": "Powerball only",
                "winners": 82053,
                "payout": "R7.50"
            }
        }
    },
    "Powerball Plus": {
        "1616": {  # May 17, 2025
            "Division 1": {
                "match": "5 + Powerball",
                "winners": 1,
                "payout": "R9,543,671.10"
            },
            "Division 2": {
                "match": "5 correct numbers",
                "winners": 2,
                "payout": "R98,241.30"
            },
            "Division 3": {
                "match": "4 + Powerball",
                "winners": 17,
                "payout": "R7,642.30"
            },
            "Division 4": {
                "match": "4 correct numbers",
                "winners": 281,
                "payout": "R605.90"
            },
            "Division 5": {
                "match": "3 + Powerball",
                "winners": 628,
                "payout": "R256.50"
            },
            "Division 6": {
                "match": "3 correct numbers",
                "winners": 9974,
                "payout": "R16.10"
            },
            "Division 7": {
                "match": "2 + Powerball",
                "winners": 7607,
                "payout": "R13.60"
            },
            "Division 8": {
                "match": "1 + Powerball",
                "winners": 36578,
                "payout": "R7.90"
            },
            "Division 9": {
                "match": "Powerball only",
                "winners": 55803,
                "payout": "R5.00"
            }
        },
        "1615": {  # May 14, 2025
            "Division 1": {
                "match": "5 + Powerball",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "5 correct numbers",
                "winners": 1,
                "payout": "R156,928.20"
            },
            "Division 3": {
                "match": "4 + Powerball",
                "winners": 15,
                "payout": "R7,107.10"
            },
            "Division 4": {
                "match": "4 correct numbers",
                "winners": 256,
                "payout": "R547.80"
            },
            "Division 5": {
                "match": "3 + Powerball",
                "winners": 583,
                "payout": "R239.70"
            },
            "Division 6": {
                "match": "3 correct numbers",
                "winners": 9453,
                "payout": "R14.70"
            },
            "Division 7": {
                "match": "2 + Powerball",
                "winners": 7091,
                "payout": "R12.60"
            },
            "Division 8": {
                "match": "1 + Powerball",
                "winners": 34240,
                "payout": "R7.30"
            },
            "Division 9": {
                "match": "Powerball only",
                "winners": 53051,
                "payout": "R5.00"
            }
        }
    },
    "Daily Lottery": {
        "2258": {  # May 18, 2025
            "Division 1": {
                "match": "5 correct numbers",
                "winners": 3,
                "payout": "R158,741.70"
            },
            "Division 2": {
                "match": "4 correct numbers",
                "winners": 242,
                "payout": "R1,144.80"
            },
            "Division 3": {
                "match": "3 correct numbers",
                "winners": 7364,
                "payout": "R25.00"
            },
            "Division 4": {
                "match": "2 correct numbers",
                "winners": 71442,
                "payout": "R5.00"
            }
        },
        "2257": {  # May 17, 2025
            "Division 1": {
                "match": "5 correct numbers",
                "winners": 2,
                "payout": "R223,859.40"
            },
            "Division 2": {
                "match": "4 correct numbers",
                "winners": 262,
                "payout": "R898.30"
            },
            "Division 3": {
                "match": "3 correct numbers",
                "winners": 7587,
                "payout": "R25.00"
            },
            "Division 4": {
                "match": "2 correct numbers",
                "winners": 70652,
                "payout": "R5.00"
            }
        },
        "2256": {  # May 16, 2025
            "Division 1": {
                "match": "5 correct numbers",
                "winners": 0,
                "payout": "R0.00"
            },
            "Division 2": {
                "match": "4 correct numbers",
                "winners": 301,
                "payout": "R820.90"
            },
            "Division 3": {
                "match": "3 correct numbers",
                "winners": 9032,
                "payout": "R25.00"
            },
            "Division 4": {
                "match": "2 correct numbers",
                "winners": 80892,
                "payout": "R5.00"
            }
        },
        "2255": {  # May 15, 2025
            "Division 1": {
                "match": "5 correct numbers",
                "winners": 1,
                "payout": "R410,520.60"
            },
            "Division 2": {
                "match": "4 correct numbers",
                "winners": 264,
                "payout": "R912.30"
            },
            "Division 3": {
                "match": "3 correct numbers",
                "winners": 8157,
                "payout": "R25.00"
            },
            "Division 4": {
                "match": "2 correct numbers",
                "winners": 76453,
                "payout": "R5.00"
            }
        }
    }
}

def update_prize_divisions():
    """
    Update lottery results with division prize information.
    """
    updated_count = 0
    
    with app.app_context():
        for lottery_type, draws in PRIZE_DIVISIONS.items():
            for draw_number, divisions in draws.items():
                # Find this draw in the database
                lottery_result = LotteryResult.query.filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                # If not found with exact name, try with Lotto instead of Lottery
                if not lottery_result and "Lottery" in lottery_type:
                    alt_type = lottery_type.replace("Lottery", "Lotto")
                    lottery_result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                # If still not found, try PowerBall variation
                if not lottery_result and "Powerball" in lottery_type:
                    alt_type = lottery_type.replace("Powerball", "PowerBall")
                    lottery_result = LotteryResult.query.filter_by(
                        lottery_type=alt_type,
                        draw_number=draw_number
                    ).first()
                
                if lottery_result:
                    # Update the divisions data
                    lottery_result.divisions = json.dumps(divisions)
                    updated_count += 1
                    logger.info(f"Updated divisions for {lottery_type} draw {draw_number}")
                else:
                    logger.warning(f"Could not find {lottery_type} draw {draw_number} in database")
        
        # Commit all changes
        db.session.commit()
    
    return updated_count

def main():
    """Main function to update prize divisions."""
    try:
        print("Updating lottery prize divisions...")
        updated = update_prize_divisions()
        print(f"Successfully updated {updated} lottery draws with prize division information.")
        
        # Now let's verify one of the draws to ensure it worked
        with app.app_context():
            lottery_result = LotteryResult.query.filter_by(
                lottery_type="Powerball",
                draw_number="1615"
            ).first()
            
            if lottery_result and lottery_result.divisions:
                divisions = json.loads(lottery_result.divisions)
                print("\nExample of division data:")
                print(f"Powerball Draw #1615 - Divisions:")
                for name, details in divisions.items():
                    print(f"  {name}: {details['match']} - {details['winners']} winners - {details['payout']}")
            else:
                print("\nCould not verify divisions update.")
        
    except Exception as e:
        logger.error(f"Error updating prize divisions: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()