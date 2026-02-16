# Microservices Architecture with API Gateway

**SLIIT - IT4020 Modern Topics in IT - Lab 3**  
Building a microservices architecture using Python FastAPI with API Gateway pattern.

##  Architecture
```
Client
  ↓ (JWT Authentication)
  ↓
API Gateway (Port 8000)
├── Authentication Layer
├── Request Logging Middleware
├── Enhanced Error Handling
  ↓
  ├─→ Student Service (Port 8001)
  └─→ Course Service (Port 8002)
```

## 📁 Project Structure
```
microservices-fastapi/
├── student-service/          # Student microservice
│   ├── models.py
│   ├── data_service.py
│   ├── service.py
│   └── main.py
├── course-service/           # Course microservice
│   ├── models.py
│   ├── data_service.py
│   ├── service.py
│   └── main.py
├── gateway/                  # API Gateway
│   └── main.py
├── requirements.txt
└── README.md
```

##  Setup & Installation

### Prerequisites
- Python 3.8+
- pip



4. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Running the Application

**Terminal 1 - Student Service:**
```bash
cd student-service
uvicorn main:app --reload --port 8001
```

**Terminal 2 - Course Service:**
```bash
cd course-service
uvicorn main:app --reload --port 8002
```

**Terminal 3 - API Gateway:**
```bash
cd gateway
uvicorn main:app --reload --port 8000
```

##  Authentication

All API endpoints require JWT authentication.



### Use Token:
Add header to all requests:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

##  API Endpoints

### Gateway Root
- `GET /` - Gateway information

### Authentication
- `POST /auth/login` - Get JWT token

### Students (via Gateway)
- `GET /gateway/students` - List all students
- `GET /gateway/students/{id}` - Get student by ID
- `POST /gateway/students` - Create student
- `PUT /gateway/students/{id}` - Update student
- `DELETE /gateway/students/{id}` - Delete student

### Courses (via Gateway)
- `GET /gateway/courses` - List all courses
- `GET /gateway/courses/{id}` - Get course by ID
- `POST /gateway/courses` - Create course
- `PUT /gateway/courses/{id}` - Update course
- `DELETE /gateway/courses/{id}` - Delete course

##  Testing

Access interactive API documentation:
- Gateway: http://localhost:8000/docs
- Student Service: http://localhost:8001/docs
- Course Service: http://localhost:8002/docs


- Service-specific error handling

##  Technologies Used

- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **HTTPx** - Async HTTP client
- **PyJWT** - JWT authentication
- **Python 3.13**

##  Lab Details

- **Course:** IT4020 - Modern Topics in IT
- **Lab:** Practical 3
- **Topic:** Building Microservices Architecture with API Gateway
- **Institution:** SLIIT


