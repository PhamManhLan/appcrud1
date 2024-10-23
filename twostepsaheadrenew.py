from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import AsyncGenerator

DATABASE_URL = "postgresql+asyncpg://postgres:1906@127.0.0.1/secondCRUD"

# Tạo engine và session
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# Định nghĩa model SQLAlchemy
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# Định nghĩa Pydantic models cho request và response
class ItemCreate(BaseModel):
    name: str

class ItemRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# Tạo FastAPI app
app = FastAPI()

# Tạo database (nên làm trong một script riêng để quản lý)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency để lấy session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# CRUD Operations

@app.post("/items/", response_model=ItemRead)
async def create_item(item: ItemCreate, session: AsyncSession = Depends(get_session)):
    new_item = Item(name=item.name)
    session.add(new_item)
    await session.commit()
    await session.refresh(new_item)
    return new_item

@app.get("/items/{item_id}", response_model=ItemRead)
async def read_item(item_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, item_data: ItemCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    item.name = item_data.name
    await session.commit()
    return item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await session.delete(item)
    await session.commit()
    return {"detail": "Item deleted"}

# Khởi động ứng dụng và tạo bảng (nên chạy một lần riêng biệt)
@app.on_event("startup")
async def startup_event():
    await init_db()
