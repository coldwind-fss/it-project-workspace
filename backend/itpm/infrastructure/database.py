"""Parameterised Core statements, explicit transactions, no runtime DDL."""
from pathlib import Path
import json
from sqlalchemy import create_engine, MetaData, Table, text, select, insert, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

CONTRACTS = Path(__file__).resolve().parents[3] / 'contracts'


def catalog(connection):
    queries = json.loads((CONTRACTS / 'catalog-queries.json').read_text('utf-8'))
    result = {'formatVersion': 1}
    for key, query in queries.items():
        result[key] = [dict(x) for x in connection.execute(text(query)).mappings()]
    for f in result['functions']:
        f['source'] = f['source'].replace('\r\n', '\n').replace('\r', '\n')
    return result


def schema_difference(actual):
    expected = json.loads((CONTRACTS / 'schema-manifest.json').read_text('utf-8'))
    return [key for key in expected if expected[key] != actual.get(key)]

def schema_details(actual):
    expected=json.loads((CONTRACTS/'schema-manifest.json').read_text('utf-8'));details=[]
    for group in ['tables','columns','indexes','constraints','functions']:
        def identifier(row):return (row.get('table',''),row.get('name',''),row.get('arguments',''))
        before={identifier(r):r for r in expected[group]};after={identifier(r):r for r in actual.get(group,[])}
        for key in before.keys()|after.keys():
            if key not in before:details.append({'group':group,'object':list(key),'change':'unexpected'})
            elif key not in after:details.append({'group':group,'object':list(key),'change':'missing'})
            else:
                fields=[f for f in before[key].keys()|after[key].keys() if before[key].get(f)!=after[key].get(f)]
                if fields:details.append({'group':group,'object':list(key),'change':'attributes','fields':fields})
    return details


class Database:
    def __init__(self, settings):
        self.settings = settings
        self.engine = create_engine(settings.database_url, pool_size=settings.pool_size,
            max_overflow=0, pool_timeout=settings.pool_timeout, pool_pre_ping=True,
            connect_args={'connect_timeout': 3}, hide_parameters=True)
        self.metadata = MetaData()
        self.aliases = json.loads((CONTRACTS / 'column-aliases.json').read_text('utf-8'))
        self.ready_code = 'DATABASE_UNAVAILABLE'
        self.differences=[]

    def check(self):
        try:
            with self.engine.connect() as c:
                adopted=catalog(c);self.differences=schema_details(adopted)
                if schema_difference(adopted):
                    self.ready_code = 'SCHEMA_MISMATCH'
                    return False
                if not self.metadata.tables:
                    self.metadata.reflect(bind=c, schema='public')
                role = c.execute(text("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user")).one()
                ddl = c.execute(text("SELECT has_schema_privilege(current_user,'public','CREATE')")).scalar()
                database_ddl=c.execute(text("SELECT has_database_privilege(current_user,current_database(),'CREATE') OR has_database_privilege(current_user,current_database(),'TEMPORARY')")).scalar()
                if any(role) or ddl or database_ddl:
                    self.ready_code = 'UNSAFE_DATABASE_ROLE'
                    return False
            self.ready_code = ''
            return True
        except Exception:
            self.ready_code = 'DATABASE_UNAVAILABLE'
            return False

    def table(self, name):
        return self.metadata.tables['public.' + name]

    def row(self, row):
        return {self.aliases.get(k, k): v for k, v in row.items()} if row is not None else None

    def close(self):
        self.engine.dispose()


class UnitOfWork:
    def __init__(self, database, dispatcher):
        self.database, self.dispatcher = database, dispatcher
        self.events = []
        self.on_rollback = []

    def __enter__(self):
        self.connection = self.database.engine.connect()
        self.transaction = self.connection.begin()
        return self
    def lock_key(self,namespace,key):
        import hashlib
        from sqlalchemy import func
        digest=hashlib.blake2b((namespace+':'+key).encode('utf-8'),digest_size=8).digest()
        self.connection.execute(select(func.pg_advisory_xact_lock(int.from_bytes(digest,'big',signed=True))))

    def __exit__(self, typ, value, tb):
        try:
            if typ is None:
                try:
                    self.transaction.commit()
                except Exception:
                    self.events.clear()
                    for cleanup in self.on_rollback:cleanup()
                    raise
            else:
                self.transaction.rollback()
                self.events.clear()
                for cleanup in self.on_rollback:cleanup()
        finally:
            self.connection.close()
        if typ is None:
            self.dispatcher.dispatch(self.events)


class Repository:
    """A module may write only tables in its declared ownership set."""
    def __init__(self, database, tables):
        self.db, self.owned = database, frozenset(tables)

    def table(self, name):
        if name not in self.owned:
            raise ValueError('private table access')
        return self.db.table(name)

    def rows(self, uow, statement):
        return [self.db.row(x) for x in uow.connection.execute(statement).mappings()]

    def one(self, uow, statement):
        return self.db.row(uow.connection.execute(statement).mappings().first())

    def get(self, uow, table, key, active=False, lock=False):
        t = self.table(table)
        pk = list(t.primary_key.columns)[0]
        stmt = select(t).where(pk == key)
        if active and 'deletedat' in t.c:
            from sqlalchemy import func
            stmt = stmt.where(func.coalesce(t.c.deletedat, '') == '')
        if lock:
            stmt = stmt.with_for_update()
        return self.one(uow, stmt)

    def values(self, table, values):
        t = self.table(table)
        if any(k.lower() not in t.c for k in values):
            raise ValueError('undeclared column')
        return {k.lower(): v for k, v in values.items()}

    def add(self, uow, table, values, conflict=None):
        t = self.table(table)
        stmt = pg_insert(t).values(**self.values(table, values))
        if conflict:
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict)
        uow.connection.execute(stmt)

    def change(self, uow, table, key, values):
        if values:
            t = self.table(table)
            uow.connection.execute(update(t).where(list(t.primary_key.columns)[0] == key).values(**self.values(table, values)))

    def remove(self, uow, table, key):
        t = self.table(table)
        uow.connection.execute(delete(t).where(list(t.primary_key.columns)[0] == key))

    def find(self,uow,table,filters=None,active=False,order=None,limit=None,lock=False):
        from sqlalchemy import func,literal_column
        t=self.table(table);stmt=select(t)
        for key,value in (filters or {}).items():stmt=stmt.where(t.c[key.lower()]==value)
        if active and 'deletedat' in t.c:stmt=stmt.where(func.coalesce(t.c.deletedat,'')=='')
        for key,descending in order or []:
            column=literal_column('ctid') if key=='rowid' else t.c[key.lower()]
            stmt=stmt.order_by(column.desc() if descending else column)
        if limit:stmt=stmt.limit(limit)
        if lock:stmt=stmt.with_for_update()
        return self.rows(uow,stmt)
