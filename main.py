from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


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


DATABASE_URL = "sqlite:///test.db"

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_session)]


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_sample_data():
    with Session(engine) as session:
        spu_beamline = Beamline(name="SPU")
        qua_beamline = Beamline(name="QUA")

        session.add_all([spu_beamline, qua_beamline])
        session.commit()

        admin_role = Role(name="admin")
        expert_role = Role(name="expert")
        user_role = Role(name="user")
        advanced_role = Role(name="advanced")
        observer_role = Role(name="observer")
        session.add_all(
            [admin_role, expert_role, user_role, advanced_role, observer_role]
        )

        bob = User(name="Bob", username="bob")
        alice = User(name="Alice", username="alice")
        charlie = User(name="Charlie", username="charlie")

        session.add_all([bob, alice, charlie])
        session.commit()

        session.add_all(
            [
                UserRole(
                    user_id=bob.id, role_id=admin_role.id, beamline_id=spu_beamline.id
                ),
                UserRole(
                    user_id=alice.id,
                    role_id=expert_role.id,
                    beamline_id=qua_beamline.id,
                ),
                UserRole(
                    user_id=charlie.id,
                    role_id=user_role.id,
                    beamline_id=spu_beamline.id,
                ),
                UserRole(
                    user_id=charlie.id,
                    role_id=advanced_role.id,
                    beamline_id=qua_beamline.id,
                ),
                UserRole(
                    user_id=charlie.id,
                    role_id=observer_role.id,
                    beamline_id=qua_beamline.id,
                ),
            ]
        )
        session.commit()


description = """
Authorization control layer for each beamline's **bluesky** setup.

This service provides an API to manage users' roles across beamline's experimental
control setup that are built on top of bluesky `queue-server` and `http-server`
services.

"""


app = FastAPI(
    title="sophys-auth",
    description=description,
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_sample_data()


@app.get("/users/")
async def read_users(session: SessionDependency) -> list[User]:
    users = session.exec(select(User)).all()

    return users


@app.get("/instrument/{beamline_name}/qserver/access/")
async def read_beamline_roles(beamline_name: str, session: SessionDependency):
    role_dict = {}
    beamline = session.exec(
        select(Beamline).where(Beamline.name == beamline_name)
    ).first()
    if not beamline:
        raise HTTPException(status_code=404, detail="Beamline not found")

    # Select user roles for the specified beamline
    user_roles = session.exec(
        select(UserRole)
        .where(UserRole.beamline_id == beamline.id)
        .join(UserRole.user)
        .join(UserRole.role)
    ).all()

    for user_role in user_roles:
        username = user_role.user.username
        role_name = user_role.role.name
        if role_name not in role_dict:
            role_dict[role_name] = {}
        role_dict[role_name][username] = {}

    return role_dict


@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, session: SessionDependency):
    db_user = User(**user.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/roles/", response_model=Role)
async def create_role(role: RoleCreate, session: SessionDependency):
    db_role = Role(**role.model_dump())
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


@app.post("/beamlines/", response_model=Beamline)
async def create_beamline(beamline: BeamlineCreate, session: SessionDependency):
    db_beamline = Beamline(**beamline.model_dump())
    session.add(db_beamline)
    session.commit()
    session.refresh(db_beamline)
    return db_beamline


@app.post("/register/")
async def assign_role(user_role: UserRoleAssign, session: SessionDependency):
    user = session.exec(select(User).where(User.username == user_role.username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = session.exec(select(Role).where(Role.name == user_role.role)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    beamline = session.exec(
        select(Beamline).where(Beamline.name == user_role.beamline)
    ).first()
    if not beamline:
        raise HTTPException(status_code=404, detail="Beamline not found")

    db_user_role = UserRole(user_id=user.id, role_id=role.id, beamline_id=beamline.id)
    session.add(db_user_role)
    session.commit()
    return {
        "message": f"Role {role.name} assigned to {user.name} for beamline {beamline.name}"
    }
