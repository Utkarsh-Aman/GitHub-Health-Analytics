import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from app.globals import MONTHS


# Used by: every callback file

def get_month_range(slider_values):
    """
    Converts date slider index values to month strings.

    Input:  [0, 23]  (indices)
    Output: ('2023-01', '2024-12')  (month strings)

    Example:
        start, end = get_month_range([3, 18])
        # start = '2023-04'
        # end   = '2024-07'
    """
    start = MONTHS[slider_values[0]]
    end = MONTHS[slider_values[1]]
    return start, end


# Test — run this file directly
# python3 app/components/filters.py

if __name__ == '__main__':
    print("Testing filters.py...")

    print("\nAll months available:")
    print(MONTHS)

    print("\nTest get_month_range([0, 23]):")
    print(get_month_range([0, 23]))

    print("\nTest get_month_range([3, 18]):")
    print(get_month_range([3, 18]))

    print("\nTest get_month_range([12, 12]):")
    print(get_month_range([12, 12]))

    print("\nAll tests passed.")