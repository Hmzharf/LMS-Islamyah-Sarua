"""
Utility functions for reports
"""
from datetime import datetime


def get_current_academic_year():
    """
    Get current academic year
    Returns: tuple (year_start, year_end)
    Example: (2024, 2025)
    """
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if current_month >= 7:  # Juli - Desember
        return (current_year, current_year + 1)
    else:  # Januari - Juni
        return (current_year - 1, current_year)


def get_academic_years_list(count=5):
    """
    Generate list of academic years
    Args:
        count: number of years to generate (default: 5)
    Returns: list of tuples [(2022, 2023), (2023, 2024), ...]
    """
    current_year_start, current_year_end = get_current_academic_year()
    
    years = []
    for i in range(-2, count - 2):
        year_start = current_year_start + i
        year_end = year_start + 1
        years.append((year_start, year_end))
    
    return years


def format_academic_year(year_start, year_end):
    """
    Format academic year for display
    Args:
        year_start: int
        year_end: int
    Returns: str (example: "2024/2025")
    """
    return f"{year_start}/{year_end}"


def parse_academic_year(academic_year_str):
    """
    Parse academic year string
    Args:
        academic_year_str: str (example: "2024/2025")
    Returns: tuple (year_start, year_end)
    """
    if '/' in academic_year_str:
        year_start, year_end = academic_year_str.split('/')
        return (int(year_start), int(year_end))
    return get_current_academic_year()


def get_month_year_from_academic_year(month, academic_year_str):
    """
    Get actual year based on month and academic year
    Args:
        month: int (1-12)
        academic_year_str: str (example: "2024/2025")
    Returns: int (actual year)
    """
    year_start, year_end = parse_academic_year(academic_year_str)
    
    # Juli (7) - Desember (12) = year_start
    # Januari (1) - Juni (6) = year_end
    if month >= 7:
        return year_start
    else:
        return year_end
