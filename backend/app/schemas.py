from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, model_validator
from enum import Enum
from datetime import datetime

class GroupMemberRead(BaseModel):
    id: int
    user: "UserSummary"

class GroupMemberCreate(BaseModel):
    user_id: int

class UserSummary(BaseModel):
    id: int
    name: str

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)

class GoogleLogin(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GroupCreate(BaseModel):
    name:str

class GroupRead(BaseModel):
    id: int
    name: str

class SplitMethod(str, Enum):
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"

class SplitPartipant(BaseModel):
    user_id: int
    percentage: Decimal|None = None
    amount: Decimal|None = Field(default = None, ge=0, max_digits=10, decimal_places=2)

class ExpenseRead(BaseModel):
    id: int
    group: GroupRead
    title: str
    paid_by_user: UserSummary
    total_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    created_at: datetime

class ExpenseCreate(BaseModel):
    title: str
    paid_by_user_id: int
    total_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    split_method: SplitMethod = SplitMethod.EQUAL
    split_participants: list[SplitPartipant] | None = None

    @model_validator(mode="after")
    def validate_split_participants(self):
        if self.split_method in {
            SplitMethod.EXACT,
            SplitMethod.PERCENTAGE
        } and not self.split_participants:
            raise ValueError("split_participants is required for EXACT and PERCENTAGE split methods")
        return self

class ExpenseSplitsCreate(BaseModel):
    user_id: int
    amount_owed: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    amount_paid: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

class ExpenseSplitsRead(BaseModel):
    id: int
    user: UserSummary
    amount_owed: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    amount_paid: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

class SettlementRead(BaseModel):
    from_user: UserSummary
    to_user: UserSummary
    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

class SettlementStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SettlementCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

