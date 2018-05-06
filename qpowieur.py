import datetime
import io
import os
import time

import jinja2
import PIL.Image
import sqlalchemy


CORE_DATA_EPOCH = datetime.datetime(2001, 1, 1, 0, 0, 0)
Z_PRIMARYKEY = 'Z_PRIMARYKEY'
ZDATA = 'ZDATA'
ZINDEX = 'ZINDEX'
SKIP_COLUMNS = set([
    ZDATA,
    ZINDEX,
])


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


class ZEntityDB():
    def __init__(self, path_to_sqlite_file):
        self.path_to_sqlite_file = str(path_to_sqlite_file)
        self._init_check_file()
        self._init_prepare_db_objs()
        self._init_load_entity_types()

    def _init_check_file(self):
        if not os.path.isfile(self.path_to_sqlite_file):
            # Do not create db file if it does not already exist
            raise FileNotFoundError(self.path_to_sqlite_file)

    def _init_prepare_db_objs(self):
        url = 'sqlite:///'+self.path_to_sqlite_file
        self.engine = sqlalchemy.create_engine(url)
        self.metadata = sqlalchemy.MetaData()
        self.metadata.reflect(bind=self.engine)

    def execute(self, object, *multiparams, **params):
        return self.engine.execute(object, *multiparams, **params)

    def _init_load_entity_types(self):
        zpk = self.metadata.tables[Z_PRIMARYKEY]
        only_base_types = zpk.c.Z_SUPER == 0
        stmt = zpk.select(only_base_types)
        result = self.execute(stmt)
        self.registry = EntityTypeRegistry()
        for row in result.fetchall():
            self.registry.register(row, self.metadata.tables)
        self.entity_types = frozenset(self.registry.values())

        for entity_type in self.entity_types:
            entity_type.complete_initialization(
                registry=self.registry,
                entity_types=self.entity_types,
            )

    def fetchall(self, entity_type):
        entity_type = self.registry[entity_type]
        child_statements = entity_type.reference_statements
        result = self.execute(entity_type.stmt)
        for row in result.fetchall():
            entity = construct_entity_from_row(entity_type, row)
            for child_entity_type, child_stmt in child_statements.items():
                child_prefix = child_entity_type.prefix
                key = child_prefix + '_list'
                children = list()
                child_result = self.execute(child_stmt, refpk=entity._pk)
                for child_row in child_result.fetchall():
                    child_entity = construct_entity_from_row(
                        child_entity_type,
                        child_row,
                    )
                    children.append(child_entity)
                setattr(entity, key, children)
            yield entity


def main(argv, out, err):
    zedb = ZEntityDB('SousChef.recipedb')

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('.'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )
    template = env.get_template('recipe_template.html')
    out_folder = 'out.' + str(time.time())
    os.mkdir(out_folder)
    for recipe in zedb.fetchall('Recipe'):
        slug = slugify(recipe.name)
        filename = 'recipe.' + slug
        replace_images(recipe, out_folder, filename)
        out_filename = filename + '.html'
        print(out_filename)
        with open(os.path.join(out_folder, out_filename), 'w') as out:
            template.stream(recipe=recipe).dump(out)
    print(out_folder)


def replace_images(entity, folder, filename):
    traverse_entity_tree(entity, replace_image, [filename], folder=folder)


def replace_image(entity, trail, folder):
    data = getattr(entity, 'data', None)
    if data is None:
        return True
    image_filename = '.'.join(trail) + '.png'
    with PIL.Image.open(io.BytesIO(data)) as image:
        image.save(os.path.join(folder, image_filename), 'PNG')
    delattr(entity, 'data')
    entity.filename = image_filename


def traverse_entity_tree(entity, callback, trail, **kwargs):
    if not isinstance(entity, Entity):
        return
    if not callback(entity, trail, **kwargs):
        return
    v = vars(entity)
    for key, value in v.items():
        if key[-5:] == '_list':
            i = 1
            for item in value:
                traverse_entity_tree(
                    item,
                    callback,
                    trail + [key, str(i)],
                    **kwargs
                )
                i += 1
        else:
            traverse_entity_tree(value, callback, trail + [key], **kwargs)


class Entity(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def construct_entity_from_row(entity_type, row):
    breakout = dict()
    for key, value in row.items():
        prefix, name = key.split('_', 1)
        if prefix not in breakout:
            breakout[prefix] = dict()
        breakout[prefix][name] = value

    this_prefix = entity_type.prefix

    for prefix, data in breakout.items():
        if prefix == this_prefix:
            continue
        child_entity = Entity(**breakout[prefix])
        breakout[this_prefix][prefix] = child_entity

    entity = Entity(**breakout[this_prefix])

    return entity


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

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._unaskedfor.add(key)

    def _safe(self, key):
        value = self[key]
        if type(value) == bytes:
            if len(value) > 10:
                value = value[:5]+b'...'+value[-5:]
        return value


def slugify(s):
    return ''.join([
        (_.casefold() if _.isalnum() else '-') for _ in s
    ])


def build_statement_for_entity_type(
    start_type,
    registry,
    entity_types,
    referenced_type=None,
):
    start_table = start_type.table

    colqueue = list(start_table.c)
    selections = set()
    selectfroms = set()
    joins = None

    while len(colqueue) > 0:
        thiscol = colqueue.pop(0)
        if joins is None:
            joins = thiscol.table
        other_entity_type = registry.get(thiscol.name, None)
        if other_entity_type is None:
            selections.add(thiscol)
            selectfroms.add(thiscol.table)
            continue
        if other_entity_type == referenced_type:
            continue
        other = other_entity_type.table
        if other in selectfroms:
            continue
        joins = joins.outerjoin(other, thiscol == other.c.Z_PK)
        for othercol in other.c:
            if othercol in selections:
                continue
            colqueue.append(othercol)

    labeled = list()
    for selection in selections:
        db_objects = [selection.table, selection]
        label_parts = []
        for db_object in db_objects:
            oname = db_object.name[1:].lower()
            if oname in SKIP_COLUMNS:
                oname = '_' + oname
            label_parts.append(oname)
        label = '_'.join(label_parts)
        labeled.append(selection.label(label))

    stmt = sqlalchemy.sql.select(labeled).select_from(joins)

    if referenced_type is not None:
        refpk = sqlalchemy.bindparam('refpk')
        where = start_type.table.c[referenced_type.table.name] == refpk
        stmt = stmt.where(where)

    if ZINDEX in start_type.table.c:
        stmt = stmt.order_by(sqlalchemy.asc(start_type.table.c.ZINDEX))

    return stmt


def build_statements_for_references(start_type, registry, entity_types):
    stmts = dict()

    for referencing_entity_type in entity_types:
        if referencing_entity_type == start_type:
            continue
        if start_type.table.name not in referencing_entity_type.table.c:
            continue
        stmt = build_statement_for_entity_type(
            start_type=referencing_entity_type,
            registry=registry,
            entity_types=entity_types,
            referenced_type=start_type,
        )
        stmts[referencing_entity_type] = stmt

    return stmts


class EntityType():
    def __init__(self, z_ent, z_name, table):
        self.ent = z_ent
        self.name = z_name
        self.prefix = z_name.lower()
        self.table = table

    def __repr__(self):
        # return 'EntityType({ent},{name})'.format(vars(self))
        return str(vars(self))

    def complete_initialization(self, registry, entity_types):
        stmt = build_statement_for_entity_type(
            start_type=self,
            registry=registry,
            entity_types=entity_types,
        )
        self.stmt = stmt
        stmts = build_statements_for_references(
            start_type=self,
            registry=registry,
            entity_types=entity_types,
        )
        self.reference_statements = stmts


class EntityTypeRegistry(dict):
    def register(self, row, tables):
        z_ent = row.Z_ENT
        z_name = row.Z_NAME
        table_name = 'Z' + z_name.upper()
        et = EntityType(z_ent, z_name, tables[table_name])
        for key in [
            et,
            et.ent,
            et.name,
            et.prefix,
            et.table,
            et.table.name,
        ]:
            self[key] = et


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv, sys.stdout, sys.stderr))
