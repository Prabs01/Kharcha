from enum import Enum
from datetime import datetime, UTC
from sqlmodel import Field, Session, SQLModel, create_engine, Relationship
from sqlalchemy.orm import Mapped
from fastapi import Depends
from typing import Annotated
from pydantic import EmailStr, model_validator


class GroupMember(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    group: Mapped["Group"] = Relationship(back_populates="memberships", sa_relationship_kwargs={"overlaps": "members,user"})
    user: Mapped["User"] = Relationship(back_populates="memberships", sa_relationship_kwargs={"overlaps": "groups,members"})

    def to_read(self, user):
        assert self.id is not None

        return GroupMemberRead(
            id = self.id,
            user = UserRead.model_validate(user)
        )

class GroupMemberRead(SQLModel):
    id: int
    user: "UserRead"

class GroupMemberCreate(SQLModel):
    user_id: int


class User(SQLModel, table = True):
    id: int|None = Field(default = None, primary_key = True)
    name: str = Field(index = True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str

    # explain: this is a one to many relationship where one user can pay for many expenses. 
    # The back_populates is used to specify the attribute on the other side of the relationship that will be used to access the related objects. 
    # In this case, it will be the "paid_by_user" attribute on the Expenses model.
    expenses_paid: Mapped[list["Expenses"]] = Relationship(back_populates="paid_by_user") 
    groups : Mapped[list["Group"]] = Relationship(back_populates="members", link_model=GroupMember, sa_relationship_kwargs={"overlaps": "memberships,user,group"})
    memberships: Mapped[list[GroupMember]] = Relationship(back_populates="user", sa_relationship_kwargs={"overlaps": "groups"})
    splits: Mapped[list["ExpenseSplits"]] = Relationship(back_populates="user")

    def to_read(self):
        assert self.id is not None

        return UserRead(
            id = self.id,
            name = self.name,
            email = self.email
        )


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

    members: Mapped[list[User]] = Relationship(back_populates="groups", link_model=GroupMember, sa_relationship_kwargs={"overlaps": "memberships,user"})
    memberships: Mapped[list[GroupMember]] = Relationship(back_populates="group", sa_relationship_kwargs={"overlaps": "members,user"})
    expenses: Mapped[list["Expenses"]] = Relationship(back_populates="group")


class GroupCreate(SQLModel):
    name:str

class GroupRead(SQLModel):
    id: int
    name: str

class SplitMethod(str, Enum):
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"

class SplitPartipant(SQLModel):
    user_id: int
    percentage:float | None = None
    amount: float | None = None

class Expenses(SQLModel, table = True):
    id: int| None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    paid_by_user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    title: str = Field(index = True)
    total_amount: float = Field(ge = 0)
    created_at: datetime = Field(default_factory= lambda : datetime.now(UTC))

    paid_by_user : Mapped["User"] = Relationship(back_populates="expenses_paid")
    splits: Mapped[list["ExpenseSplits"]] = Relationship(back_populates="expense")
    group: Mapped["Group"] = Relationship(back_populates="expenses")

    def to_read(self, paid_by_user, group):
        assert self.id is not None
        assert self.paid_by_user is not None

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
    split_method: SplitMethod = Field(default=SplitMethod.EQUAL)
    split_participants: list[SplitPartipant] | None = None

    @model_validator(mode = "after")
    def validate_split_participants(self):
        if self.split_method in {
            SplitMethod.EXACT,
            SplitMethod.PERCENTAGE
        } and not self.split_participants:
            raise ValueError("split_participants is required for EXACT and PERCENTAGE split methods")

        return self

class ExpenseSplits(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    expense_id: int = Field(foreign_key="expenses.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    amount_owed: float
    amount_paid: float
 
    expense: Mapped["Expenses"] = Relationship(back_populates="splits")
    user: Mapped["User"] = Relationship(back_populates="splits")

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

