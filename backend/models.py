from datetime import datetime, UTC
from sqlmodel import Field, Session, SQLModel, create_engine
from fastapi import Depends
from typing import Annotated
from pydantic import EmailStr

class User(SQLModel, table = True):
    id: int|None = Field(default = None, primary_key = True)
    name: str = Field(index = True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str

class UserRead(SQLModel): #UseOut is just a output schema so 'table = False'
    id: int
    name: str
    email: EmailStr

class UserCreate(SQLModel):
    name: str
    email: EmailStr
    password: str

class Group(SQLModel, table= True):
    id: int|None = Field(default= True, primary_key=True)
    name: str = Field(index= True) #putting index makes filtering more efficient later but slows down insert/deletes

class GroupCreate(SQLModel):
    name:str

class GroupRead(SQLModel):
    id: int
    name: str

class GroupMember(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    def to_read(self, user):
        assert self.id is not None

        return GroupMemberRead(
            id = self.id,
            user = UserRead.model_validate(user)
        )

class GroupMemberRead(SQLModel):
    id: int
    user: UserRead

class GroupMemberCreate(SQLModel):
    user_id: int

class Expenses(SQLModel, table = True):
    id: int| None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    paid_by_user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    title: str = Field(index = True)
    total_amount: float = Field(ge = 0)
    created_at: datetime = Field(default_factory= lambda : datetime.now(UTC))

    def to_read(self, paid_by_user, group):
        assert self.id is not None

        return ExpenseRead(
            id = self.id,
            group = GroupRead.model_validate(group),
            paid_by_user = UserRead.model_validate(paid_by_user),
            title = self.title,
            total_amount= self.total_amount,
            created_at= self.created_at
        )



class ExpenseRead(SQLModel):
    id: int
    group: GroupRead
    paid_by_user: UserRead
    title: str
    total_amount: float
    created_at: datetime

class ExpenseCreate(SQLModel):
    paid_by_user_id: int
    title: str 
    total_amount: float = Field(ge = 0)

class ExpenseSplits(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    expense_id: int = Field(foreign_key="expenses.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    amount_owed: float
    amount_paid: float

    def to_read(self, user):
        assert self.id is not None

        return ExpenseSplitsRead(
            id = self.id,
            user = UserRead.model_validate(user),
            amount_owed = self.amount_owed,
            amount_paid=self.amount_paid
        )

class ExpenseSplitsCreate(SQLModel):
    user_id: int
    amount_owed: float
    amount_paid: float

class ExpenseSplitsRead(SQLModel):
    id: int
    user: UserRead
    amount_owed: float
    amount_paid: float


sqlite_file_name = "database.db" 
sqlite_url  = f"sqlite:///{sqlite_file_name}"


#Using check_same_thread=False allows FastAPI to use the same SQLite database in different threads. This is necessary as one single request could use more than one thread (for example in dependencies).
connect_arg= {"check_same_thread" : False} 
engine = create_engine(sqlite_url, connect_args=connect_arg, pool_pre_ping=True) #pool_pre_ping checks if the connection is alive before using it, and reconnects if it's not. This can help prevent issues with stale connections in a long-running application.



def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


# reusable alias
SessionDep = Annotated[Session, Depends(get_session)]

