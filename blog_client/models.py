from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from pydantic import TypeAdapter

class Post(BaseModel):
    userId: int
    id: int
    title: str
    body: str

class Comment(BaseModel):
    postId: int
    id: int
    name: str
    email: EmailStr
    body: str

class PostWithComments(BaseModel):
    post: Post
    comments: list[Comment] = Field(default_factory=list)

PostsAdapter = TypeAdapter(list[Post])
CommentsAdapter = TypeAdapter(list[Comment])
