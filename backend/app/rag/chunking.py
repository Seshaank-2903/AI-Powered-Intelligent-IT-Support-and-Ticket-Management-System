import re

def chunk_text(text: str, max_chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """
    Splits text into overlapping chunks.
    Attempts to split on paragraphs or sentences to maintain semantic boundaries.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if len(current_chunk) + len(para) <= max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If a single paragraph is too large, force split it
            if len(para) > max_chunk_size:
                words = para.split(' ')
                sub_chunk = ""
                for word in words:
                    if len(sub_chunk) + len(word) <= max_chunk_size:
                        sub_chunk += word + " "
                    else:
                        chunks.append(sub_chunk.strip())
                        sub_chunk = word + " "
                current_chunk = sub_chunk
            else:
                current_chunk = para + "\n\n"
                
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Add overlapping (naive approach for this prototype)
    overlapped_chunks = []
    for i in range(len(chunks)):
        chunk = chunks[i]
        if i > 0:
            # Prepend overlap from previous chunk
            prev_chunk = chunks[i-1]
            overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            chunk = overlap_text + " " + chunk
        overlapped_chunks.append(chunk)

    return overlapped_chunks
