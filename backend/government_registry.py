from typing import List

# Demo government registry data.
# In production, replace this with a secure government data lookup.
GOVERNMENT_RECORDS: List[dict] = [
    {
        "name": "Rahul Sharma",
        "email": "rahul.sharma@test.com",
        "aadhar": "123412341234",
    },
    {
        "name": "Priya Verma",
        "email": "priya.verma@test.com",
        "aadhar": "234523452345",
    },
    {
        "name": "Amit Patel",
        "email": "amit.patel@test.com",
        "aadhar": "345634563456",
    },
    {
        "name": "Sneha Kulkarni",
        "email": "sneha.kulkarni@test.com",
        "aadhar": "456745674567",
    },
    {
        "name": "Arjun Singh",
        "email": "arjun.singh@test.com",
        "aadhar": "567856785678",
    },
    {
        "name": "Neha Gupta",
        "email": "neha.gupta@test.com",
        "aadhar": "678967896789",
    },
    {
        "name": "Vikram Joshi",
        "email": "vikram.joshi@test.com",
        "aadhar": "789078907890",
    },
    {
        "name": "Pooja Mehta",
        "email": "pooja.mehta@test.com",
        "aadhar": "890189018901",
    },
    {
        "name": "Karan Malhotra",
        "email": "karan.malhotra@test.com",
        "aadhar": "901290129012",
    },
    {
        "name": "Anjali Desai",
        "email": "anjali.desai@test.com",
        "aadhar": "112233445566",
    },
]


def verify_citizen_record(name: str, email: str, aadhar: str) -> bool:
    normalized_name = (name or "").strip().lower()
    normalized_email = (email or "").strip().lower()
    normalized_aadhar = (aadhar or "").strip()

    for record in GOVERNMENT_RECORDS:
        if (
            record["name"].strip().lower() == normalized_name
            and record["email"].strip().lower() == normalized_email
            and record["aadhar"].strip() == normalized_aadhar
        ):
            return True

    return False
