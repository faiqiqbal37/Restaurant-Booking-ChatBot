from datetime import datetime, timedelta
import re

def parse_natural_date(date_str: str) -> str:
    """
    Parses a natural language date string into 'YYYY-MM-DD' format.
    Handles various common formats and relative dates.
    """
    if not date_str:
        return ""
    
    # Standardize the input string
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    # Handle relative dates
    if date_str in ["today"]:
        return today.strftime('%Y-%m-%d')
    
    if date_str in ["tomorrow"]:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    
    if "yesterday" in date_str:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Handle "this weekend" (assume Saturday)
    if "this weekend" in date_str or "weekend" in date_str:
        days_ahead = 5 - today.weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Handle specific weekdays with "next" or "this"
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in date_str:
            if "next" in date_str:
                # Next occurrence of this weekday
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif "this" in date_str:
                # This week's occurrence (could be past)
                days_ahead = day_num - today.weekday()
                if days_ahead < 0:
                    days_ahead += 7  # Next week if already passed
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            else:
                # Just the day name - assume next occurrence
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Handle "in X days"
    days_match = re.search(r'in (\d+) days?', date_str)
    if days_match:
        days = int(days_match.group(1))
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Handle "X days from now"
    days_match = re.search(r'(\d+) days? from now', date_str)
    if days_match:
        days = int(days_match.group(1))
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Handle formats like "Dec 25", "December 25", "25 Dec"
    month_patterns = [
        (r'(\d{1,2})\s+(jan|january)', lambda d, m: f"{today.year}-01-{d:02d}"),
        (r'(\d{1,2})\s+(feb|february)', lambda d, m: f"{today.year}-02-{d:02d}"),
        (r'(\d{1,2})\s+(mar|march)', lambda d, m: f"{today.year}-03-{d:02d}"),
        (r'(\d{1,2})\s+(apr|april)', lambda d, m: f"{today.year}-04-{d:02d}"),
        (r'(\d{1,2})\s+(may)', lambda d, m: f"{today.year}-05-{d:02d}"),
        (r'(\d{1,2})\s+(jun|june)', lambda d, m: f"{today.year}-06-{d:02d}"),
        (r'(\d{1,2})\s+(jul|july)', lambda d, m: f"{today.year}-07-{d:02d}"),
        (r'(\d{1,2})\s+(aug|august)', lambda d, m: f"{today.year}-08-{d:02d}"),
        (r'(\d{1,2})\s+(sep|september)', lambda d, m: f"{today.year}-09-{d:02d}"),
        (r'(\d{1,2})\s+(oct|october)', lambda d, m: f"{today.year}-10-{d:02d}"),
        (r'(\d{1,2})\s+(nov|november)', lambda d, m: f"{today.year}-11-{d:02d}"),
        (r'(\d{1,2})\s+(dec|december)', lambda d, m: f"{today.year}-12-{d:02d}"),
    ]
    
    for pattern, formatter in month_patterns:
        match = re.search(pattern, date_str)
        if match:
            day = int(match.group(1))
            if 1 <= day <= 31:
                result = formatter(day, match.group(2))
                # If the date has passed this year, assume next year
                try:
                    parsed_date = datetime.strptime(result, '%Y-%m-%d').date()
                    if parsed_date < today:
                        year = today.year + 1
                        result = result.replace(str(today.year), str(year))
                    return result
                except ValueError:
                    continue
    
    # Handle reverse format: "Jan 25", "January 25"
    reverse_patterns = [
        (r'(jan|january)\s+(\d{1,2})', lambda m, d: f"{today.year}-01-{d:02d}"),
        (r'(feb|february)\s+(\d{1,2})', lambda m, d: f"{today.year}-02-{d:02d}"),
        (r'(mar|march)\s+(\d{1,2})', lambda m, d: f"{today.year}-03-{d:02d}"),
        (r'(apr|april)\s+(\d{1,2})', lambda m, d: f"{today.year}-04-{d:02d}"),
        (r'(may)\s+(\d{1,2})', lambda m, d: f"{today.year}-05-{d:02d}"),
        (r'(jun|june)\s+(\d{1,2})', lambda m, d: f"{today.year}-06-{d:02d}"),
        (r'(jul|july)\s+(\d{1,2})', lambda m, d: f"{today.year}-07-{d:02d}"),
        (r'(aug|august)\s+(\d{1,2})', lambda m, d: f"{today.year}-08-{d:02d}"),
        (r'(sep|september)\s+(\d{1,2})', lambda m, d: f"{today.year}-09-{d:02d}"),
        (r'(oct|october)\s+(\d{1,2})', lambda m, d: f"{today.year}-10-{d:02d}"),
        (r'(nov|november)\s+(\d{1,2})', lambda m, d: f"{today.year}-11-{d:02d}"),
        (r'(dec|december)\s+(\d{1,2})', lambda m, d: f"{today.year}-12-{d:02d}"),
    ]
    
    for pattern, formatter in reverse_patterns:
        match = re.search(pattern, date_str)
        if match:
            day = int(match.group(2))
            if 1 <= day <= 31:
                result = formatter(match.group(1), day)
                # If the date has passed this year, assume next year
                try:
                    parsed_date = datetime.strptime(result, '%Y-%m-%d').date()
                    if parsed_date < today:
                        year = today.year + 1
                        result = result.replace(str(today.year), str(year))
                    return result
                except ValueError:
                    continue
    
    # Try standard formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY
    formats_to_try = [
        '%Y-%m-%d',    # 2024-12-25
        '%d/%m/%Y',    # 25/12/2024
        '%m/%d/%Y',    # 12/25/2024
        '%d-%m-%Y',    # 25-12-2024
        '%Y/%m/%d',    # 2024/12/25
        '%d.%m.%Y',    # 25.12.2024
    ]
    
    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            continue
    
    # If nothing worked, return empty string to indicate parsing failed
    return ""