import datetime

import sqlalchemy


CORE_DATA_EPOCH = datetime.datetime(2001, 1, 1, 0, 0, 0)


class TimestampEpochType(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.Float

    def process_bind_param(self, value, dialect):
        value_as_timestamp = None
        if value is not None:
            value_as_timestamp = (value - CORE_DATA_EPOCH).total_seconds()
        return value_as_timestamp

    def process_result_value(self, value, dialect):
        value_as_datetime = None
        if value is not None:
            value_as_timedelta = datetime.timedelta(seconds=float(value))
            value_as_datetime = CORE_DATA_EPOCH + value_as_timedelta
        return value_as_datetime


@sqlalchemy.event.listens_for(sqlalchemy.Table, "column_reflect")
def setup_coredata_timestamp(inspector, table, column_info):
    if isinstance(column_info['type'], sqlalchemy.types.TIMESTAMP):
        column_info['type'] = TimestampEpochType()


def main(argv, out, err):
    url = 'sqlite:///SousChef.recipedb'
    engine = sqlalchemy.create_engine(url)
    meta = sqlalchemy.MetaData()
    meta.reflect(bind=engine)
    zpk = meta.tables['Z_PRIMARYKEY']
    stmt = zpk.select(zpk.c.Z_SUPER == 0)
    result = engine.execute(stmt)
    registry = EntityTypeRegistry()
    for row in result.fetchall():
        registry.register(row, meta.tables)
    recipe_type = registry['Recipe']
    zrecipe = recipe_type.table
    stmt = zrecipe.select()
    print(stmt)


class EntityType():
    def __init__(self, z_ent, z_name, table):
        self.ent = z_ent
        self.name = z_name
        self.table = table

    def __repr__(self):
        # return 'EntityType({ent},{name})'.format(vars(self))
        return str(vars(self))


class EntityTypeRegistry(dict):
    def register(self, row, tables):
        z_ent = row.Z_ENT
        z_name = row.Z_NAME
        table_name = 'Z' + z_name.upper()
        et = EntityType(z_ent, z_name, tables[table_name])
        self[z_ent] = et
        self[z_name] = et


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, sys.stdout, sys.stderr))
