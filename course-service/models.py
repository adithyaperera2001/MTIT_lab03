from pydantic import BaseModel
from typing import Optional

class Course(BaseModel):
    id: int
    name: str
    code: str
    credits: int
    instructor: str

class CourseCreate(BaseModel):
    name: str
    code: str
    credits: int
    instructor: str

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    credits: Optional[int] = None
    instructor: Optional[str] = None