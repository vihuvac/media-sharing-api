from contextlib import asynccontextmanager

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Post, create_db_and_tables, get_async_session
from app.schemas import PostCreate, PostResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


text_posts = {
    1: {
        "title": "Getting Started with FastAPI",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python. It is easy to learn and very powerful.",
    },
    2: {
        "title": "Why Use Python for Web APIs",
        "content": "Python offers a clean syntax, a huge ecosystem of libraries, and excellent community support for backend development.",
    },
    3: {
        "title": "Understanding RESTful Endpoints",
        "content": "RESTful APIs are based on standard HTTP methods such as GET, POST, PUT, and DELETE to manage resources.",
    },
    4: {
        "title": "FastAPI vs Flask",
        "content": "While Flask is lightweight and flexible, FastAPI provides built-in data validation and automatic API documentation.",
    },
    5: {
        "title": "Working with Path Parameters",
        "content": "Path parameters allow you to pass dynamic values in the URL and are commonly used to identify specific resources.",
    },
    6: {
        "title": "Using Query Parameters Effectively",
        "content": "Query parameters are useful for filtering, sorting, and paginating API responses without changing the endpoint path.",
    },
    7: {
        "title": "Request Validation with Pydantic",
        "content": "Pydantic models ensure that incoming request data is validated and parsed correctly before reaching your logic.",
    },
    8: {
        "title": "Handling Errors Gracefully",
        "content": "Proper error handling improves user experience by returning clear messages and appropriate HTTP status codes.",
    },
    9: {
        "title": "Automatic API Documentation",
        "content": "FastAPI automatically generates interactive API documentation using Swagger UI and ReDoc.",
    },
    10: {
        "title": "Deploying a FastAPI Application",
        "content": "You can deploy FastAPI apps using tools like Uvicorn, Docker, and cloud platforms such as AWS or Azure.",
    },
}


@app.get(
    "/posts",
    response_model=list[PostResponse],
    summary="Get a list of posts",
    tags=["Posts"],
)
def get_posts(
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of posts to return.",
    ),
) -> list[PostResponse]:
    return [PostResponse(**post) for post in list(text_posts.values())[:limit]]


@app.post(
    "/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post.",
    tags=["Posts"],
)
def create_post(post: PostCreate) -> PostResponse:
    new_post = PostResponse(
        title=post.title,
        content=post.content,
    )
    text_posts[max(text_posts.keys()) + 1] = new_post.model_dump()
    return new_post


@app.get(
    "/posts/{id}",
    response_model=PostResponse,
    summary="Get a post by ID.",
    tags=["Posts"],
    responses={
        404: {
            "description": "Post not found",
            "content": {"application/json": {"example": {"detail": "Post not found."}}},
        }
    },
)
def get_post(id: int):
    if id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found.")

    return text_posts.get(id)


@app.post(
    "/files/upload",
    summary="Upload a file with a caption.",
    tags=["Files"],
)
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    new_post = Post(
        caption=caption,
        url=f"/files/{file.filename}",
        file_type=file.content_type,
        file_name=file.filename,
    )
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return {"id": new_post.id, "caption": new_post.caption, "url": new_post.url}


@app.get(
    "/files",
    summary="Get a list of uploaded files.",
    tags=["Files"],
)
async def get_files(
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
            }
        )
    return {
        "posts": posts_data,
    }
