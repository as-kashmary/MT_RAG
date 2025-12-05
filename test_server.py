import fastapi
import uvicorn

from DB_Routes.Company_routes import router as company_router
from DB_Routes.User_routes import router as user_router
from DB_Routes.File_routes import router as file_router
from DB_Routes.query_routes import router as query_router

app= fastapi.FastAPI()

app.include_router(company_router)
app.include_router(user_router)
app.include_router(file_router)
app.include_router(query_router)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)