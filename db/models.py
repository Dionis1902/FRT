from enum import Enum

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, ARRAY, BIGINT, TEXT, TIMESTAMP, ENUM, BYTEA


class Status(Enum):
    PROGRESS = 'progress'
    ERROR = 'error'
    STOPPED = 'stopped'
    KILLED = 'killed'
    FINISHED = 'finished'


metadata = sqlalchemy.MetaData()

tasks = sqlalchemy.Table(
    'tasks',
    metadata,
    sqlalchemy.Column('id', INTEGER, primary_key=True),
    sqlalchemy.Column('name', TEXT),
    sqlalchemy.Column('start_time', TIMESTAMP, server_default=func.now()),
    sqlalchemy.Column('status', ENUM(*[e.value for e in Status], name='status_enum'), server_default=Status.PROGRESS.value),
    sqlalchemy.Column('accounts', ARRAY(BIGINT), server_default='{}')
)

accounts = sqlalchemy.Table(
    'accounts',
    metadata,
    sqlalchemy.Column('id', INTEGER, primary_key=True),
    sqlalchemy.Column('user_id', BIGINT, unique=True),
    sqlalchemy.Column('session_string', TEXT),
    sqlalchemy.Column('first_name', TEXT, nullable=False),
    sqlalchemy.Column('last_name', TEXT),
    sqlalchemy.Column('username', TEXT),
    sqlalchemy.Column('bio', TEXT),
    sqlalchemy.Column('county_code', TEXT),
    sqlalchemy.Column('phone_number', TEXT),
    sqlalchemy.Column('is_premium', BOOLEAN),
    sqlalchemy.Column('spam_block', TEXT,  server_default='No'),
    sqlalchemy.Column('proxy', TEXT, default=None),
    sqlalchemy.Column('photos', ARRAY(TEXT), server_default='{}'),
    sqlalchemy.Column('in_live_task', BOOLEAN, server_default='false'),
)


settings = sqlalchemy.Table(
    'settings',
    metadata,
    sqlalchemy.Column('id', INTEGER, primary_key=True),
    sqlalchemy.Column('name', TEXT, unique=True),
    sqlalchemy.Column('value', BYTEA),
)
