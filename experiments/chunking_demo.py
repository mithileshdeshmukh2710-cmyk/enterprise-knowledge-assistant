from backend.app.chunking import create_chunks

text = """
Employees are entitled to annual leave.
Employees must submit leave applications
through the HR portal.

Managers are responsible for approving
leave requests.

Emergency leave requires immediate
notification to the manager.
""" * 20

chunks = create_chunks(
    text,
    chunk_size=200,
    overlap=40
)

print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks):

    print(f"\n--- CHUNK {i + 1} ---")

    print(chunk)

    print("Characters:", len(chunk))