"""
Date validation utilities for resume entries.
Provides reliable date parsing, validation, and consistency checking.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import re

try:
    from dateutil.parser import parse as parse_date
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print("⚠️ python-dateutil not available. Install with: pip install python-dateutil")

def parse_resume_date(date_str: str) -> Optional[datetime]:
    """
    Parse various date formats commonly used in resumes.
    Supports: 2023-01, 2023, Jan 2023, January 2023, etc.
    """
    if not date_str or date_str.lower() in ['present', 'current', 'ongoing']:
        return None  # Present/ongoing dates
    
    # Clean the date string
    date_str = date_str.strip()
    
    # Handle different formats
    formats_to_try = [
        '%Y-%m',        # 2023-01
        '%Y-%m-%d',     # 2023-01-15
        '%Y',           # 2023
        '%m/%Y',        # 01/2023
        '%m-%Y',        # 01-2023
        '%B %Y',        # January 2023
        '%b %Y',        # Jan 2023
    ]
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If dateutil is available, try its flexible parsing
    if DATEUTIL_AVAILABLE:
        try:
            return parse_date(date_str, default=datetime(1900, 1, 1))
        except Exception:
            pass
    
    print(f"⚠️ Could not parse date: {date_str}")
    return None

def validate_date_range(start_date: str, end_date: str, entry_name: str = "") -> List[str]:
    """
    Validate that a date range is logical and realistic.
    """
    errors = []
    
    start_dt = parse_resume_date(start_date) if start_date else None
    end_dt = parse_resume_date(end_date) if end_date else datetime.now()
    
    if not start_dt:
        errors.append(f"Invalid start date format: {start_date}")
        return errors
    
    # Check if the start date is too far in the future
    future_limit = datetime.now()
    if DATEUTIL_AVAILABLE:
        future_limit = future_limit + relativedelta(months=6)

    if start_dt > future_limit:
        errors.append(f"Start date {start_date} is too far in the future for {entry_name}")
    
    # Check if end date is before start date
    if end_dt and start_dt > end_dt:
        errors.append(f"End date {end_date} is before start date {start_date} for {entry_name}")
    
    # Check for unreasonably long durations (more than 50 years)
    if end_dt:
        duration_years = (end_dt - start_dt).days / 365.25
        if duration_years > 50:
            errors.append(f"Duration of {duration_years:.1f} years seems unrealistic for {entry_name}")
    
    return errors

def validate_experience_dates(experience_list: List[Dict[str, Any]]) -> List[str]:
    """
    Validate dates across all experience entries.
    """
    errors = []
    
    for i, exp in enumerate(experience_list):
        company = exp.get('company', f'Experience {i+1}')
        position = exp.get('position', '')
        start_date = exp.get('start_date', '')
        end_date = exp.get('end_date', '')
        
        entry_name = f"{position} at {company}" if position else company
        
        # Validate individual date range
        range_errors = validate_date_range(start_date, end_date, entry_name)
        errors.extend(range_errors)
    
    # Check for overlapping positions (same company)
    for i, exp1 in enumerate(experience_list):
        for j, exp2 in enumerate(experience_list[i+1:], i+1):
            if exp1.get('company') == exp2.get('company'):
                overlap_errors = check_date_overlap(exp1, exp2)
                errors.extend(overlap_errors)
    
    return errors

def validate_education_dates(education_list: List[Dict[str, Any]]) -> List[str]:
    """
    Validate dates in education entries.
    """
    errors = []
    
    for i, edu in enumerate(education_list):
        institution = edu.get('institution', f'Education {i+1}')
        degree = edu.get('degree', '')
        start_date = edu.get('start_date', '')
        end_date = edu.get('end_date', '')
        
        entry_name = f"{degree} at {institution}" if degree else institution
        
        # Validate individual date range
        range_errors = validate_date_range(start_date, end_date, entry_name)
        errors.extend(range_errors)
        
        # Check reasonable duration for degree programs
        start_dt = parse_resume_date(start_date)
        end_dt = parse_resume_date(end_date) if end_date else datetime.now()
        
        if start_dt and end_dt:
            duration_years = (end_dt - start_dt).days / 365.25
            degree_lower = degree.lower() if degree else ''
            
            # Check realistic durations for different degree types
            if 'phd' in degree_lower or 'doctorate' in degree_lower:
                if duration_years < 3 or duration_years > 10:
                    errors.append(f"PhD duration of {duration_years:.1f} years seems unusual for {entry_name}")
            elif 'master' in degree_lower or 'ms' in degree_lower or 'ma' in degree_lower:
                if duration_years < 1 or duration_years > 4:
                    errors.append(f"Master's duration of {duration_years:.1f} years seems unusual for {entry_name}")
            elif 'bachelor' in degree_lower or 'bs' in degree_lower or 'ba' in degree_lower:
                if duration_years < 3 or duration_years > 7:
                    errors.append(f"Bachelor's duration of {duration_years:.1f} years seems unusual for {entry_name}")
    
    return errors

def check_date_overlap(entry1: Dict[str, Any], entry2: Dict[str, Any]) -> List[str]:
    """
    Check if two entries have overlapping dates (potential issue for same company).
    """
    errors = []
    
    start1 = parse_resume_date(entry1.get('start_date', ''))
    end1 = parse_resume_date(entry1.get('end_date', '')) or datetime.now()
    start2 = parse_resume_date(entry2.get('start_date', ''))
    end2 = parse_resume_date(entry2.get('end_date', '')) or datetime.now()
    
    if not (start1 and start2):
        return errors
    
    # Check for overlap
    if start1 <= end2 and start2 <= end1:
        company = entry1.get('company', 'Same company')
        errors.append(f"Overlapping dates for positions at {company}")
    
    return errors

def calculate_total_experience(experience_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total years of experience from experience entries.
    """
    total_days = 0
    valid_entries = 0
    
    for exp in experience_list:
        start_dt = parse_resume_date(exp.get('start_date', ''))
        end_dt = parse_resume_date(exp.get('end_date', '')) or datetime.now()
        
        if start_dt and end_dt:
            duration = (end_dt - start_dt).days
            if duration > 0:  # Only count positive durations
                total_days += duration
                valid_entries += 1
    
    total_years = total_days / 365.25
    
    return {
        'total_years': total_years,
        'total_months': total_years * 12,
        'valid_entries': valid_entries,
        'calculation_date': datetime.now().strftime('%Y-%m-%d')
    }

def suggest_date_format_improvements(cv_sections: Dict[str, Any]) -> List[str]:
    """
    Suggest improvements to date formatting for consistency.
    """
    suggestions = []
    all_dates = []
    
    # Collect all dates from experience and education
    for section_name in ['experience', 'education']:
        if section_name in cv_sections:
            for entry in cv_sections[section_name]:
                if 'start_date' in entry:
                    all_dates.append(entry['start_date'])
                if 'end_date' in entry and entry['end_date'].lower() not in ['present', 'current']:
                    all_dates.append(entry['end_date'])
    
    # Check for consistency in date formats
    formats_found = set()
    for date_str in all_dates:
        if re.match(r'^\d{4}-\d{2}$', date_str):
            formats_found.add('YYYY-MM')
        elif re.match(r'^\d{4}$', date_str):
            formats_found.add('YYYY')
        elif re.match(r'^\d{2}/\d{4}$', date_str):
            formats_found.add('MM/YYYY')
        elif re.match(r'^[A-Za-z]+ \d{4}$', date_str):
            formats_found.add('Month YYYY')
        else:
            formats_found.add('Other')
    
    if len(formats_found) > 1:
        suggestions.append(f"Inconsistent date formats found: {', '.join(formats_found)}. Consider using YYYY-MM format consistently.")
    
    return suggestions 