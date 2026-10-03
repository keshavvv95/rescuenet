from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, complaints, video, zones #, adoption, admin, users_manage, notifications

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="RescueNet - Stray Animal Welfare Management Platform API",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(complaints.router, prefix=f"{settings.API_V1_STR}/complaints", tags=["complaints"])
app.include_router(video.router, prefix=f"{settings.API_V1_STR}/video", tags=["video"])
app.include_router(zones.router, prefix=f"{settings.API_V1_STR}/zones", tags=["zones"])
# app.include_router(adoption.router, prefix=f"{settings.API_V1_STR}/adoption", tags=["adoption"])
# app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
# app.include_router(users_manage.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
# app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

@app.get("/")
def root():
    return {"message": "Welcome to RescueNet API"}
