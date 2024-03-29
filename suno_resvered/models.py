from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from suno_resvered.setting import DATABASE_URI

Base = declarative_base()

# 定义模型
class Cookie(Base):
    __tablename__ = 'cookies'

    id = Column(Integer, primary_key=True)
    cookie = Column(Text, nullable=False)  # Changed from String(255) to Text
    count = Column(Integer, default=5)


engine = create_engine(DATABASE_URI, echo=True)

# 创建表
# Base.metadata.create_all(engine)

# 创建Session类
Session = sessionmaker(bind=engine)
