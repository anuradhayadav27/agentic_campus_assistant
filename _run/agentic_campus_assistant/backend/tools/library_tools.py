import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from agentic_campus_assistant.backend.database.db import get_connection

def search_library_books(query: str, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Search university library catalog by book title, author, or keyword.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT book_id, title, author, category, isbn, total_copies, available_copies, shelf_location
        FROM library_books
        WHERE (UPPER(title) LIKE UPPER(?) OR UPPER(author) LIKE UPPER(?) OR UPPER(category) LIKE UPPER(?))
    """
    params = [f"%{query}%", f"%{query}%", f"%{query}%"]

    if category:
        sql += " AND UPPER(category) LIKE UPPER(?)"
        params.append(f"%{category}%")

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    books = []
    for r in rows:
        books.append({
            "book_id": r["book_id"],
            "title": r["title"],
            "author": r["author"],
            "category": r["category"],
            "isbn": r["isbn"],
            "total_copies": r["total_copies"],
            "available_copies": r["available_copies"],
            "shelf_location": r["shelf_location"],
            "status": "IN_STOCK" if r["available_copies"] > 0 else "ALL_COPIES_ISSUED"
        })

    return {
        "success": True,
        "query": query,
        "books_found": len(books),
        "books": books
    }

def reserve_library_book(student_id: str, book_id: str) -> Dict[str, Any]:
    """
    Reserve a book from the campus library.
    If copies are zero, returns waitlist status and suggests related titles.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT book_id, title, category, available_copies, shelf_location FROM library_books WHERE book_id = ? OR UPPER(title) LIKE UPPER(?)", (book_id, f"%{book_id}%"))
    book_row = cursor.fetchone()

    if not book_row:
        conn.close()
        return {
            "success": False,
            "error_type": "BOOK_NOT_FOUND",
            "message": f"Book '{book_id}' does not exist in library registry."
        }

    actual_book_id = book_row["book_id"]
    title = book_row["title"]
    avail = book_row["available_copies"]
    shelf = book_row["shelf_location"]
    category = book_row["category"]

    if avail <= 0:
        # Find related books in the same category that ARE available
        cursor.execute("SELECT book_id, title, author, available_copies FROM library_books WHERE category = ? AND available_copies > 0", (category,))
        alt_books = [{"book_id": r["book_id"], "title": r["title"], "author": r["author"]} for r in cursor.fetchall()]
        conn.close()

        return {
            "success": False,
            "error_type": "COPIES_EXHAUSTED",
            "message": f"All copies of '{title}' are currently issued out.",
            "waitlist_available": True,
            "suggested_alternatives": alt_books
        }

    # Reserve copy
    reservation_id = f"LIB-{random.randint(1000, 9999)}"
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    pickup_deadline = (now + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M")

    # Decrement available copies
    cursor.execute("UPDATE library_books SET available_copies = available_copies - 1 WHERE book_id = ?", (actual_book_id,))

    cursor.execute("""
        INSERT INTO library_reservations (
            reservation_id, student_id, book_id, book_title, shelf_location,
            pickup_deadline, loan_duration_days, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 14, 'Active - Ready for Pickup', ?)
    """, (reservation_id, student_id, actual_book_id, title, shelf, pickup_deadline, created_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "reservation_id": reservation_id,
        "book_id": actual_book_id,
        "title": title,
        "shelf_location": shelf,
        "pickup_deadline": pickup_deadline,
        "loan_duration_days": 14,
        "status": "Reserved (Hold active for 48 hours)",
        "message": f"'{title}' reserved! Present Token #{reservation_id} at {shelf} before {pickup_deadline}."
    }
