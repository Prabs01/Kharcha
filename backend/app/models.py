from decimal import Decimal
from datetime import datetime, UTC

from sqlmodel import (
    Field, 
    SQLModel, 
    Relationship
)

from sqlalchemy.orm import Mapped
from pydantic import EmailStr

from app.schemas import (
    GroupMemberRead,
    UserSummary,
    UserRead,
    GroupRead,
    ExpenseRead,
    ExpenseSplitsRead,
    SettlementStatus,
    FriendshipStatus
)


class GroupMember(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")

    group: Mapped["Group"] = Relationship(back_populates="memberships", sa_relationship_kwargs={"overlaps": "members,user", "cascade": "all, delete"})
    user: Mapped["User"] = Relationship(back_populates="memberships", sa_relationship_kwargs={"overlaps": "groups,members", "cascade": "all, delete"})

    def to_read(self, user):
        assert self.id is not None

        return GroupMemberRead(
            id = self.id,
            user = UserSummary.model_validate(user.to_summary())
        )


class User(SQLModel, table = True):
    id: int|None = Field(default = None, primary_key = True)
    name: str = Field(index = True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str | None = Field(nullable=True)

    is_google_account: bool = Field(default=False) #This field is used to identify if the user is created through Google login or not. This can be useful for handling authentication and password management for users created through Google login.

    # explain: this is a one to many relationship where one user can pay for many expenses. 
    # The back_populates is used to specify the attribute on the other side of the relationship that will be used to access the related objects. 
    # In this case, it will be the "paid_by_user" attribute on the Expenses model.
    expenses_paid: Mapped[list["Expenses"]] = Relationship(back_populates="paid_by_user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}) #This means that when a user is deleted, all associated expenses will also be deleted. This helps maintain data integrity and prevents orphaned records in the database.
    groups : Mapped[list["Group"]] = Relationship(back_populates="members", link_model=GroupMember, sa_relationship_kwargs={"overlaps": "memberships,user,group", "cascade": "all, delete"})
    memberships: Mapped[list[GroupMember]] = Relationship(back_populates="user", sa_relationship_kwargs={"overlaps": "groups", "cascade": "all, delete-orphan"})
    splits: Mapped[list["ExpenseSplits"]] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}) #This means that when a user is deleted, all associated splits will also be deleted. This helps maintain data integrity and prevents orphaned records in the database.

    def to_read(self):
        assert self.id is not None

        return UserRead(
            id = self.id,
            name = self.name,
            email = self.email
        )

    def to_summary(self):
        assert self.id is not None

        return UserSummary(
            id = self.id,
            name = self.name
        )


class Group(SQLModel, table= True):
    id: int|None = Field(default= None, primary_key=True)
    name: str = Field(index= True) #putting index makes filtering more efficient later but slows down insert/deletes

    members: Mapped[list[User]] = Relationship(back_populates="groups", link_model=GroupMember, sa_relationship_kwargs={"overlaps": "memberships,user", "cascade": "all, delete"})
    memberships: Mapped[list[GroupMember]] = Relationship(back_populates="group", sa_relationship_kwargs={"overlaps": "members,user", "cascade": "all, delete-orphan"})
    expenses: Mapped[list["Expenses"]] = Relationship(back_populates="group", sa_relationship_kwargs={"cascade": "all, delete-orphan"}) #This means that when a group is deleted, all associated expenses will also be deleted. This helps maintain data integrity and prevents orphaned records in the database.
    settlements: Mapped[list["Settlement"]] = Relationship(back_populates="group", sa_relationship_kwargs={"cascade": "all, delete-orphan"}) #This means that when a group is deleted, all associated settlements will also be deleted. This helps maintain data integrity and prevents orphaned records in the database.

    def to_read(self):
        assert self.id is not None

        return GroupRead(
            id = self.id,
            name = self.name
        )


class Expenses(SQLModel, table = True):
    id: int| None = Field(default= None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", ondelete="CASCADE")
    paid_by_user_id: int = Field(foreign_key="user.id", ondelete="RESTRICT") 
    title: str = Field(index = True)
    total_amount: Decimal = Field(ge = 0, max_digits=10, decimal_places=2)
    created_at: datetime = Field(default_factory= lambda : datetime.now(UTC))

    paid_by_user : Mapped["User"] = Relationship(back_populates="expenses_paid")
    splits: Mapped[list["ExpenseSplits"]] = Relationship(back_populates="expense", sa_relationship_kwargs={"cascade": "all, delete-orphan"})#This means that when an expense is deleted, all associated splits will also be deleted. This helps maintain data integrity and prevents orphaned records in the database.
    group: Mapped["Group"] = Relationship(back_populates="expenses")

    def to_read(self, paid_by_user, group):
        assert self.id is not None
        assert self.paid_by_user is not None

        return ExpenseRead(
            id = self.id,
            group = GroupRead.model_validate(group.to_read()),
            paid_by_user = UserSummary.model_validate(paid_by_user.to_summary()),
            title = self.title,
            total_amount= self.total_amount,
            created_at= self.created_at
        )



class ExpenseSplits(SQLModel, table = True):
    id: int|None = Field(default= None, primary_key=True)
    expense_id: int = Field(foreign_key="expenses.id", ondelete="CASCADE", nullable=False) #expense_id should not be nullable because every split must be associated with an expense
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    amount_owed: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    amount_paid: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
 
    expense: Mapped["Expenses"] = Relationship(back_populates="splits")
    user: Mapped["User"] = Relationship(back_populates="splits")

    def to_read(self, user):
        assert self.id is not None

        return ExpenseSplitsRead(
            id = self.id,
            user = UserSummary.model_validate(user.to_summary()),
            amount_owed = self.amount_owed,
            amount_paid=self.amount_paid
        )


class Settlement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    group_id: int = Field(
        foreign_key="group.id",
        ondelete="CASCADE"
    )

    from_user_id: int = Field(
        foreign_key="user.id",
        ondelete="RESTRICT"
    )

    to_user_id: int = Field(
        foreign_key="user.id",
        ondelete="RESTRICT"
    )

    status: SettlementStatus = Field(default=SettlementStatus.COMPLETED)

    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    settled_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    group: Mapped["Group"] = Relationship(back_populates="settlements")

class FriendshipRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    sender_id: int = Field(
        foreign_key="user.id",
        ondelete="CASCADE"
    )
    receiver_id: int = Field(
        foreign_key="user.id",
        ondelete="CASCADE"
    )

    status: FriendshipStatus = Field(default=FriendshipStatus.PENDING)

class Friendship(SQLModel, table=True):
    user_low_id: int = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        primary_key=True
    )

    user_high_id: int = Field(
        foreign_key="user.id",
        ondelete="CASCADE",
        primary_key=True
    )