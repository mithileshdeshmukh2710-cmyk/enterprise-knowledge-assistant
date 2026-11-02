import fitz


doc = fitz.open()

page = doc.new_page()

page.insert_text(
    (72, 72),
    "Enterprise Knowledge Assistant\n\n"
    "This is a sample employee policy document.\n\n"
    "Employees can work remotely up to two days "
    "per week, subject to manager approval.\n\n"
    "Employees must follow company security policies."
)

doc.save("sample_documents/company_policy.pdf")

doc.close()

print("Sample PDF created successfully!")