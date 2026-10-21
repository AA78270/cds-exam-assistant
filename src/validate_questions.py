EXPECTED_COUNTS = {"english": 120, "general studies": 120, "mathematics": 100}


def validate(docs, subject: str) -> None:
    n = len(docs)
    exp = EXPECTED_COUNTS.get(subject)
    if exp and n != exp:
        print(f"  WARNING: {subject} has {n} questions, expected {exp}")

    no_options = [d.metadata["question_number"] for d in docs
                  if "(a)" not in d.page_content.lower() and "(b)" not in d.page_content.lower()]
    if no_options:
        print(f"  WARNING: no options detected in Q{no_options[:15]}")

    tiny = [d.metadata["question_number"] for d in docs if len(d.page_content) < 40]
    if tiny:
        print(f"  WARNING: very short chunks for Q{tiny[:15]}")