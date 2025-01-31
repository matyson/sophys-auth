from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    username: str
    roles: list["UserRole"] = Relationship(back_populates="user")


class Beamline(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    users: list["UserRole"] = Relationship(back_populates="beamline")


class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    users: list["UserRole"] = Relationship(back_populates="role")


class UserRole(SQLModel, table=True):
    user_id: int = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: int = Field(default=None, foreign_key="role.id", primary_key=True)
    beamline_id: int = Field(default=None, foreign_key="beamline.id", primary_key=True)

    user: User = Relationship(back_populates="roles")
    role: Role = Relationship(back_populates="users")
    beamline: Beamline = Relationship(back_populates="users")


class UserCreate(SQLModel):
    name: str
    username: str


class RoleCreate(SQLModel):
    name: str


class BeamlineCreate(SQLModel):
    name: str


class UserRoleAssign(SQLModel):
    username: str
    role: str
    beamline: str
