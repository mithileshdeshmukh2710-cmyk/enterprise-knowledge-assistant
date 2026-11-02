import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str):
    """
    Extract text from a PDF document.
    """

    document = fitz.open(file_path)

    extracted_pages = []

    for page_number, page in enumerate(document):

        text = page.get_text()

        extracted_pages.append({
            "page": page_number + 1,
            "text": text
        })

    document.close()

    return extracted_pages