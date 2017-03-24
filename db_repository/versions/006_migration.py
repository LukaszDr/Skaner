from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
point = Table('point', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('value_x', FLOAT),
    Column('value_y', FLOAT),
    Column('Measure_id', INTEGER),
)

point = Table('point', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('value_x', Float),
    Column('value_y', Float),
    Column('measure_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['point'].columns['Measure_id'].drop()
    post_meta.tables['point'].columns['measure_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['point'].columns['Measure_id'].create()
    post_meta.tables['point'].columns['measure_id'].drop()
