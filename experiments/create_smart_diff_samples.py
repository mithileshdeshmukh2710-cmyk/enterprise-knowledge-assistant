import fitz  # PyMuPDF
from pathlib import Path

def create_pdf(filename, title, bullets):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Standard Letter size
    
    # Title
    rect_title = fitz.Rect(54, 54, 558, 90)
    page.insert_textbox(rect_title, title, fontsize=18, fontname="helv", color=(0.1, 0.15, 0.3))
    
    # Body text
    y = 110
    for bullet in bullets:
        rect_bullet = fitz.Rect(54, y, 558, y + 40)
        page.insert_textbox(rect_bullet, f"• {bullet}", fontsize=12, fontname="helv", color=(0.2, 0.2, 0.2))
        y += 45
        
    output_path = Path("sample_documents") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"Created: {output_path}")

def main():
    doc_a_sentences = [
        "Remote work: two days per week.",
        "Annual leave requires manager approval.",
        "Employees must follow company security policies."
    ]
    
    doc_b_sentences = [
        "Remote work: three days per week.",
        "Annual leave requires manager approval.",
        "Employees must follow company security policies.",
        "Employees must complete annual security training."
    ]
    
    create_pdf("company_policy_v1.pdf", "Company Policy", doc_a_sentences)
    create_pdf("company_policy_v2.pdf", "Company Policy", doc_b_sentences)

if __name__ == "__main__":
    main()

