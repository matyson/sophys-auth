from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from .models import Beamline, Role, User, UserRole

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
