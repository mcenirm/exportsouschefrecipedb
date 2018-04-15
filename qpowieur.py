import datetime
import io
import os
import time

import jinja2
import PIL.Image
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

    for entity_type in entity_types:
        stmt = build_statement_for_entity_type(
            start_type=entity_type,
            registry=registry,
            entity_types=entity_types,
        )
        entity_type.stmt = stmt

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('.'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )
    template = env.get_template('recipe_template.html')
    out_folder = 'out.' + str(time.time())
    os.mkdir(out_folder)
    recipe_entity_type = registry['Recipe']
    result = engine.execute(recipe_entity_type.stmt)
    for row in result.fetchall():
        x = X(row)
        slug = slugify(row.recipe_name)
        filename = 'recipe.' + slug
        out_filename = filename + '.html'
        image_data = row['image_data']
        if image_data is not None:
            image_filename = filename + '.png'
            with PIL.Image.open(io.BytesIO(image_data)) as image:
                image.save(os.path.join(out_folder, image_filename), 'PNG')
            x['image'] = image_filename
            del x['image_data']
        with open(os.path.join(out_folder, out_filename), 'w') as out:
            template.stream(x=x).dump(out)
        print(out_filename)
    print(out_folder)


class X(dict):
    def __init__(self, row):
        super().__init__(**row)
        self._unaskedfor = set(row.keys())
        self._counts = dict()

    def __getitem__(self, key):
        self._unaskedfor.discard(key)
        count = self._counts.get(key, 0)
        self._counts[key] = count + 1
        return super().__getitem__(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._unaskedfor.discard(key)


def slugify(s):
    return ''.join([
        (_.casefold() if _.isalnum() else '-') for _ in s
    ])


def build_statement_for_entity_type(
    start_type,
    registry,
    entity_types,
):
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

    labeled = [
        selection.label('_'.join([
            o.name[1:].lower() for o in [selection.table, selection]
        ])) for selection in selections
    ]
    stmt = sqlalchemy.sql.select(labeled).select_from(joins)
    return stmt


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
