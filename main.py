import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Project, BlogPost, ContactMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------------------------
# Portfolio API
# ---------------------------

@app.on_event("startup")
def seed_data_if_empty():
    if db is None:
        return
    # Seed projects
    if db["project"].count_documents({}) == 0:
        sample_projects = [
            {
                "title": "Realtime Chat App",
                "description": "A full‑stack chat app with websockets, auth, and group chats.",
                "tags": ["React", "FastAPI", "WebSocket", "MongoDB"],
                "github": "https://github.com/your-handle/realtime-chat",
                "live": "https://chat.example.com",
                "image": "https://images.unsplash.com/photo-1556157382-97eda2d62296?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "title": "Dev Portfolio Boilerplate",
                "description": "Modern portfolio template with 3D hero, blog, and CMS-ready backend.",
                "tags": ["Vite", "Tailwind", "Spline", "Framer Motion"],
                "github": "https://github.com/your-handle/portfolio",
                "live": "https://portfolio.example.com",
                "image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "title": "AI Code Reviewer",
                "description": "PR bot that reviews diffs, flags issues, and suggests fixes.",
                "tags": ["Python", "LLM", "GitHub Actions"],
                "github": "https://github.com/your-handle/ai-reviewer",
                "live": None,
                "image": "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop"
            },
        ]
        for p in sample_projects:
            create_document("project", p)

    # Seed blog posts
    if db["blogpost"].count_documents({}) == 0:
        sample_posts = [
            {
                "title": "How I build modern, fast developer portfolios",
                "slug": "build-fast-portfolios",
                "excerpt": "From Spline 3D hero sections to blazing‑fast Vite builds — my approach.",
                "content": "I focus on DX and UX: Vite + React, Tailwind for speed, Spline for delight, and FastAPI + Mongo for content...",
                "tags": ["portfolio", "react", "fastapi"],
                "cover_image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?q=80&w=1200&auto=format&fit=crop",
                "published_at": datetime.utcnow(),
            },
            {
                "title": "Shipping backend features fast with FastAPI",
                "slug": "shipping-with-fastapi",
                "excerpt": "Type hints, Pydantic, and speed — why FastAPI is my go‑to.",
                "content": "FastAPI lets me write clean, typed endpoints quickly. Combined with MongoDB helpers, I can ship features in hours...",
                "tags": ["python", "fastapi", "backend"],
                "cover_image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=1200&auto=format&fit=crop",
                "published_at": datetime.utcnow(),
            },
        ]
        for post in sample_posts:
            create_document("blogpost", post)

# Models for request bodies
class ContactIn(ContactMessage):
    pass

# Endpoints
@app.get("/api/projects")
def list_projects():
    items = get_documents("project", {}, limit=None)
    for i in items:
        i["_id"] = str(i.get("_id"))
    return {"items": items}

@app.get("/api/blogs")
def list_blogs():
    items = get_documents("blogpost", {}, limit=None)
    # sort by published_at desc if present
    items.sort(key=lambda x: x.get("published_at", datetime.min), reverse=True)
    for i in items:
        i["_id"] = str(i.get("_id"))
    return {"items": items}

@app.get("/api/blogs/{slug}")
def get_blog(slug: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["blogpost"].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    doc["_id"] = str(doc.get("_id"))
    return doc

@app.post("/api/contact")
def submit_contact(payload: ContactIn):
    doc_id = create_document("contactmessage", payload)
    return {"status": "ok", "id": doc_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
