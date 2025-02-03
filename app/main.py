from fastapi import FastAPI, HTTPException
from sqlmodel import select

from ._version import __version__
from .config import config
from .db import SessionDependency, create_db_and_tables, create_sample_data
from .models import (
    Beamline,
    BeamlineCreate,
    Role,
    RoleCreate,
    User,
    UserCreate,
    UserRole,
    UserRoleAssign,
)

description = """
Authorization control layer for each beamline's **bluesky** setup.

This service provides an API to manage users' roles across beamline's experimental
control setup that are built on top of bluesky `queue-server` and `http-server`
services.

"""


app = FastAPI(
    title="sophys-auth",
    description=description,
    version=__version__,
    root_path=config.root_path,
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_sample_data()


@app.get("/users")
async def read_users(session: SessionDependency) -> list[User]:
    users = session.exec(select(User)).all()

    return users


@app.get("/instrument/{beamline_name}/qserver/access")
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


@app.post("/users", response_model=User)
async def create_user(user: UserCreate, session: SessionDependency):
    db_user = User(**user.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/roles", response_model=Role)
async def create_role(role: RoleCreate, session: SessionDependency):
    db_role = Role(**role.model_dump())
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


@app.post("/beamlines", response_model=Beamline)
async def create_beamline(beamline: BeamlineCreate, session: SessionDependency):
    db_beamline = Beamline(**beamline.model_dump())
    session.add(db_beamline)
    session.commit()
    session.refresh(db_beamline)
    return db_beamline


@app.post("/register")
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
