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
    entity_types = frozenset(registry.values())

    associations = dict()
    for entity_type in entity_types:
        print(entity_type.table.name)
        for thiscol in entity_type.table.c:
            other_entity_type = registry.get(thiscol.name, None)
            if other_entity_type is None:
                continue
            associations[thiscol] = other_entity_type
            print('   ', thiscol.name)

    start_name = 'Recipe'
    start_type = registry[start_name]
    start_table = start_type.table

    colqueue = list(start_table.c)
    selections = set()
    selectfroms = set()
    joins = None

    while len(colqueue) > 0:
        thiscol = colqueue.pop(0)
        if thiscol.name.startswith('Z_'):
            continue
        if joins is None:
            joins = thiscol.table
        print(len(colqueue), thiscol.table.name, thiscol.name)
        other_entity_type = registry.get(thiscol.name, None)
        if other_entity_type is None:
            selections.add(thiscol)
            selectfroms.add(thiscol.table)
            continue
        other = other_entity_type.table
        if other in selectfroms:
            continue
        joins = joins.outerjoin(other, thiscol == other.c.Z_PK)
        for othercol in other.c:
            if othercol in selections:
                continue
            colqueue.append(othercol)
    print([_.name for _ in selectfroms])
    print([_.table.name+'.'+_.name for _ in selections])
    stmt = sqlalchemy.sql.select(selections).select_from(joins)
    print(stmt)

    colqueue = list()
    for key, entity_type in registry.items():
        if key != entity_type.ent:
            continue
        table = entity_type.table
        if table in selectfroms:
            continue
        print(table.name)
        maybes = list()
        for c in table.c:
            if c.name.startswith('Z_'):
                continue
            print('   ', c.name)


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
        self[table_name] = et


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, sys.stdout, sys.stderr))
