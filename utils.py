from typing import List, Dict, Any
import re

def format_response(ai_response: str, selected_actions: List[str], document_name: str = "Unknown Document") -> str:
    """Format the AI response for better display in Chainlit"""
    
    # Create header
    formatted_response = f"# 📄 Document Analysis Results\n\n"
    formatted_response += f"**Document:** {document_name}\n"
    formatted_response += f"**Actions Completed:** {len(selected_actions)}\n\n"
    formatted_response += "---\n\n"
    
    # Add the AI response
    formatted_response += ai_response
    
    # Add footer
    formatted_response += "\n\n---\n"
    formatted_response += "*Analysis completed by MCP Document Processing Agent*"
    
    return formatted_response

def truncate_content(content: str, max_length: int = 15000) -> str:
    """Truncate content if it's too long for API processing"""
    if len(content) <= max_length:
        return content
    
    # Try to truncate at a sentence boundary
    truncated = content[:max_length]
    last_sentence = truncated.rfind('.')
    
    if last_sentence > max_length * 0.8:  # If we can find a sentence boundary in the last 20%
        truncated = truncated[:last_sentence + 1]
    
    truncated += f"\n\n[Note: Document was truncated to {len(truncated)} characters for processing]"
    return truncated

def extract_sections(content: str) -> Dict[str, str]:
    """Extract sections from document content based on headers"""
    sections = {}
    current_section = "Introduction"
    current_content = []
    
    lines = content.split('\n')
    
    for line in lines:
        # Check if line looks like a header (all caps, short, etc.)
        if (len(line.strip()) < 100 and 
            (line.isupper() or 
             re.match(r'^[0-9]+\.', line.strip()) or
             re.match(r'^[A-Z][A-Z\s]+$', line.strip()))):
            
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = line.strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Save final section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe processing"""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized

def estimate_processing_time(content_length: int, num_actions: int) -> str:
    """Estimate processing time based on content length and number of actions"""
    # Base time estimation (very rough)
    base_time = min(content_length / 1000 * 2, 60)  # 2 seconds per 1000 chars, max 60
    action_time = num_actions * 5  # 5 seconds per action
    
    total_seconds = int(base_time + action_time)
    
    if total_seconds < 60:
        return f"~{total_seconds} seconds"
    else:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"~{minutes}m {seconds}s"

def validate_content(content: str) -> Dict[str, Any]:
    """Validate document content and return validation results"""
    validation = {
        "is_valid": True,
        "issues": [],
        "warnings": [],
        "stats": {
            "length": len(content),
            "words": len(content.split()),
            "lines": len(content.split('\n'))
        }
    }
    
    # Check for minimum content
    if len(content.strip()) < 10:
        validation["is_valid"] = False
        validation["issues"].append("Document content is too short (less than 10 characters)")
    
    # Check for maximum content
    if len(content) > 50000:
        validation["warnings"].append("Document is very long and may take significant time to process")
    
    # Check for encoding issues
    try:
        content.encode('utf-8')
    except UnicodeEncodeError:
        validation["issues"].append("Document contains characters that cannot be processed")
        validation["is_valid"] = False
    
    # Check for empty content after processing
    if not content.strip():
        validation["is_valid"] = False
        validation["issues"].append("Document appears to be empty or contains no readable text")
    
    return validation

def chunk_content(content: str, chunk_size: int = 10000, overlap: int = 500) -> List[str]:
    """Split content into overlapping chunks for processing very large documents"""
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # Try to break at a sentence boundary
        if end < len(content):
            # Look for sentence endings near the chunk boundary
            sentence_end = content.rfind('.', start + chunk_size - 200, end + 200)
            if sentence_end > start:
                end = sentence_end + 1
        
        chunk = content[start:end]
        chunks.append(chunk)
        
        # Move start position with overlap
        start = max(start + chunk_size - overlap, end)
    
    return chunks
