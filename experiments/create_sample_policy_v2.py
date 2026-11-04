import fitz
from pathlib import Path

# Revised company policy for version comparison:
# - Page 1 Remote work: increased from two days to three days per week.
# - Page 2 Annual leave: unchanged.
# - Page 3 Health insurance: added dental and vision coverage.
# - Page 4 Employee training: added leadership programs.

policies_v2 = [
    """
    Enterprise Knowledge Assistant
    Company Remote Work Policy
    Employees may work remotely up to three days per week,
    subject to manager approval. Employees must follow
    company security policies.
    """,
    """
    Annual Leave Policy
    Employees are entitled to annual leave.
    All annual leave requests require approval
    from the employee's reporting manager.
    """,
    """
    Health Insurance Policy
    Employees receive health insurance benefits.
    The company provides medical and dental coverage to eligible
    employees and their dependents.
    """,
    """
    Employee Training Policy
    The company provides technical and leadership training to employees.
    Training programs help employees improve technical
    skills and professional knowledge.
    """
]

Path("sample_documents").mkdir(parents=True, exist_ok=True)
doc = fitz.open()

for policy in policies_v2:
    page = doc.new_page()
    page.insert_text((72, 72), policy.strip())

output_path = Path("sample_documents/company_policy_v2.pdf")
doc.save(str(output_path))
doc.close()

print(f"Created {output_path} successfully!")

