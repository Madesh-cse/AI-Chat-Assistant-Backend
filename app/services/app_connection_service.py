from sqlalchemy.orm import Session # type: ignore

from app.models.app_connection import AppConnection


def get_user_app_connections(
    db: Session,
    user_id: int,
):
    return (
        db.query(AppConnection)
        .filter(
            AppConnection.user_id == user_id
        )
        .all()
    )


def connect_app(
    db: Session,
    user_id: int,
    app_id: str,
):
    connection = (
        db.query(AppConnection)
        .filter(
            AppConnection.user_id == user_id,
            AppConnection.app_id == app_id,
        )
        .first()
    )

    if connection:
        connection.connected = True
    else:
        connection = AppConnection(
            user_id=user_id,
            app_id=app_id,
            connected=True,
        )

        db.add(connection)

    db.commit()
    db.refresh(connection)

    return connection


def disconnect_app(
    db: Session,
    user_id: int,
    app_id: str,
):
    connection = (
        db.query(AppConnection)
        .filter(
            AppConnection.user_id == user_id,
            AppConnection.app_id == app_id,
        )
        .first()
    )

    if not connection:
        return None

    connection.connected = False

    db.commit()
    db.refresh(connection)

    return connection