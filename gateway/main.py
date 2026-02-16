from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from typing import Any
import logging
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway (Enhanced)", version="2.0.0")

SECRET_KEY = "your-secret-key-keep-it-secret" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

SERVICES = {
    "student": "http://localhost:8001",
    "course": "http://localhost:8002"
}

# Models for authentication
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Mock user database
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": "admin123",  
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password": "user123",
        "role": "user"
    }
}

# JWT Authentication Functions
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.info(f"Client: {request.client.host}")
    
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Process time: {process_time:.3f}s")
    
    return response

# Enhanced Error Handling
async def forward_request(service: str, path: str, method: str, **kwargs) -> Any:
    """Forward request to the appropriate microservice with enhanced error handling"""
    if service not in SERVICES:
        logger.error(f"Service not found: {service}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Service Not Found",
                "message": f"The requested service '{service}' is not available",
                "available_services": list(SERVICES.keys())
            }
        )
    
    url = f"{SERVICES[service]}{path}"
    logger.info(f"Forwarding {method} request to: {url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, **kwargs)
            elif method == "POST":
                response = await client.post(url, **kwargs)
            elif method == "PUT":
                response = await client.put(url, **kwargs)
            elif method == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                logger.error(f"Method not allowed: {method}")
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail={
                        "error": "Method Not Allowed",
                        "message": f"HTTP method '{method}' is not supported",
                        "allowed_methods": ["GET", "POST", "PUT", "DELETE"]
                    }
                )
            
            # Enhanced error handling based on status code
            if response.status_code >= 400:
                logger.warning(f"Service returned error: {response.status_code}")
                error_detail = {
                    "error": "Service Error",
                    "status_code": response.status_code,
                    "service": service,
                    "message": response.text
                }
                return JSONResponse(
                    content=error_detail,
                    status_code=response.status_code
                )
            
            logger.info(f"Request successful: {response.status_code}")
            return JSONResponse(
                content=response.json() if response.text else None,
                status_code=response.status_code
            )
            
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to service: {service}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "error": "Gateway Timeout",
                    "message": f"The service '{service}' took too long to respond",
                    "service": service
                }
            )
        except httpx.ConnectError:
            logger.error(f"Connection error to service: {service}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service Unavailable",
                    "message": f"Unable to connect to '{service}' service. Please ensure the service is running.",
                    "service": service,
                    "service_url": SERVICES[service]
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred while processing your request",
                    "details": str(e)
                }
            )

# Authentication Endpoints
@app.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Login endpoint to get JWT token"""
    user = fake_users_db.get(login_data.username)
    
    if not user or user["password"] != login_data.password:
        logger.warning(f"Failed login attempt for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Authentication Failed",
                "message": "Incorrect username or password"
            }
        )
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    logger.info(f"Successful login for user: {login_data.username}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    """Gateway root endpoint"""
    return {
        "message": "Enhanced API Gateway is running",
        "version": "2.0.0",
        "features": ["Authentication", "Request Logging", "Enhanced Error Handling"],
        "available_services": list(SERVICES.keys()),
        "endpoints": {
            "auth": "/auth/login",
            "students": "/gateway/students",
            "courses": "/gateway/courses"
        }
    }

# Student Service Routes (Protected)
@app.get("/gateway/students")
async def get_all_students(token_data: dict = Depends(verify_token)):
    """Get all students through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} accessing students list")
    return await forward_request("student", "/api/students", "GET")

@app.get("/gateway/students/{student_id}")
async def get_student(student_id: int, token_data: dict = Depends(verify_token)):
    """Get a student by ID through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} accessing student {student_id}")
    return await forward_request("student", f"/api/students/{student_id}", "GET")

@app.post("/gateway/students")
async def create_student(student_data: dict, token_data: dict = Depends(verify_token)):
    """Create a new student through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} creating new student")
    return await forward_request("student", "/api/students", "POST", json=student_data)

@app.put("/gateway/students/{student_id}")
async def update_student(student_id: int, student_data: dict, token_data: dict = Depends(verify_token)):
    """Update a student through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} updating student {student_id}")
    return await forward_request("student", f"/api/students/{student_id}", "PUT", json=student_data)

@app.delete("/gateway/students/{student_id}")
async def delete_student(student_id: int, token_data: dict = Depends(verify_token)):
    """Delete a student through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} deleting student {student_id}")
    return await forward_request("student", f"/api/students/{student_id}", "DELETE")

# Course Service Routes (Protected)
@app.get("/gateway/courses")
async def get_all_courses(token_data: dict = Depends(verify_token)):
    """Get all courses through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} accessing courses list")
    return await forward_request("course", "/api/courses", "GET")

@app.get("/gateway/courses/{course_id}")
async def get_course(course_id: int, token_data: dict = Depends(verify_token)):
    """Get a course by ID through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} accessing course {course_id}")
    return await forward_request("course", f"/api/courses/{course_id}", "GET")

@app.post("/gateway/courses")
async def create_course(course_data: dict, token_data: dict = Depends(verify_token)):
    """Create a new course through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} creating new course")
    return await forward_request("course", "/api/courses", "POST", json=course_data)

@app.put("/gateway/courses/{course_id}")
async def update_course(course_id: int, course_data: dict, token_data: dict = Depends(verify_token)):
    """Update a course through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} updating course {course_id}")
    return await forward_request("course", f"/api/courses/{course_id}", "PUT", json=course_data)

@app.delete("/gateway/courses/{course_id}")
async def delete_course(course_id: int, token_data: dict = Depends(verify_token)):
    """Delete a course through gateway (requires authentication)"""
    logger.info(f"User {token_data['sub']} deleting course {course_id}")
    return await forward_request("course", f"/api/courses/{course_id}", "DELETE")