import fitz
from pathlib import Path


policies = [
    """
    Enterprise Knowledge Assistant
    Company Remote Work Policy
    Employees can work remotely up to two days per week,
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
    The company provides medical coverage to eligible
    employees and their dependents.
    """,
    """
    Employee Training Policy
    The company provides technical training to employees.
    Training programs help employees improve technical
    skills and professional knowledge.
    """
]

# Ensure output directory exists
Path("sample_documents").mkdir(parents=True, exist_ok=True)

doc = fitz.open()

for policy in policies:
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        policy.strip()
    )

doc.save("sample_documents/company_policy.pdf")
doc.close()

print("Sample PDF created successfully with 4 pages!")
