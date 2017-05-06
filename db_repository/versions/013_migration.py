from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
photo = Table('photo', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('photopath', String(length=50)),
    Column('value_x', Float),
    Column('value_y', Float),
    Column('calculated', Boolean),
    Column('measure_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['photo'].columns['calculated'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['photo'].columns['calculated'].drop()
