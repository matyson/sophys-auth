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


app = FastAPI()


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
