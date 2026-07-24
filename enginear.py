def check_jee_eligibility(
    passing_year, class_12_percentage, category, has_pcm_subjects=True
):
    """Checks JEE Main and College Admission Eligibility based on current NTA rules."""

    # 1. Basic Eligibility to Appear for JEE Main Exam
    if passing_year not in [2024, 2025, 2026]:
        return "Not Eligible to appear for JEE Main. You must have passed Class 12 in 2024, 2025, or be appearing in 2026."

    if not has_pcm_subjects:
        return "Not Eligible. Physics and Mathematics are mandatory subjects."

    # 2. Admission Eligibility (NITs, IIITs, CFTIs)
    # General/OBC/EWS require 75%, SC/ST require 65%
    req_percentage = 75.0 if category.lower() in ["general", "obc", "ews"] else 65.0

    if class_12_percentage < req_percentage:
        return f"Eligible to appear for JEE Main exam, but NOT eligible for admission to NITs/IIITs/CFTIs (requires at least {req_percentage}% in Class 12)."

    return "Eligible to appear for JEE Main AND eligible for admission to NITs/IIITs/CFTIs!"


# --- Example Usage ---
status = check_jee_eligibility(
    passing_year=2026, class_12_percentage=82.5, category="General"
)
print(status)
