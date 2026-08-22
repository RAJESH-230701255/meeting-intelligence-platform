from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

def resolve_assignee(db: Session, assignee_name: str) -> Optional[int]:
    """
    Safely resolves an AI-extracted assignee name to a User ID.
    Returns None if the assignee is "unresolved", not found, or ambiguous.
    """
    if not assignee_name or assignee_name.lower() == "unresolved":
        return None
        
    assignee_str = assignee_name.strip()
    if len(assignee_str) < 2:
        return None # Prevent dangerous single-letter partial matches
        
    # Strategy 1: Exact case-insensitive full-name match
    exact_matches = db.query(User).filter(User.name.ilike(assignee_str)).all()
    if len(exact_matches) == 1:
        return exact_matches[0].id
        
    # Strategy 2: Safe partial match (e.g. AI extracts "Rajesh", user is "Rajesh Kumar")
    partial_matches = db.query(User).filter(User.name.ilike(f"%{assignee_str}%")).all()
    
    # Strategy 3 & 4: Handle ambiguous matches safely
    # If exactly one user matches the partial search, use it.
    # If multiple users match, it is ambiguous -> return None (leave unresolved).
    if len(partial_matches) == 1:
        return partial_matches[0].id
        
    # Strategy 5: Unresolved fallback
    return None
