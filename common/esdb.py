import json
import logging
import time

from elasticsearch.exceptions import NotFoundError

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', level=logging.ERROR)

REQUEST_TIMEOUT = 600  # 10 minutes
SCROLL_SIZE = '2h'


class NoSqlDB(object):
    """
    Interface of nosql db
    """

    def delete(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def delete_item(self, item_id):
        raise NotImplementedError

    def get_item(self, item_id):
        raise NotImplementedError

    def insert_item(self, item):
        raise NotImplementedError

    def insert_items(self, items):
        raise NotImplementedError

    def iterate_items(self):
        raise NotImplementedError

    def size(self):
        raise NotImplementedError


class ESDB(NoSqlDB):
    """Utility to access ES like a database
    """

    def __init__(self, es_client, db_name, settings=None, settings_file=None):
        """
        Initiate ES with index name
        :param es_client: es_client
        :param db_name: index name
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)

        self.es_client = es_client
        self.db_name = db_name
        self.settings = settings
        if settings is None and settings_file is not None:
            with open(settings_file) as f:
                self.settings = json.load(f)
        self.create()

    def delete(self):
        """"
        Delete db by name
        """
        self.log.info('Delete index %s', self.db_name)
        self.es_client.indices.delete(index=self.db_name, ignore_unavailable=True)

    def create(self):
        """
        Create db by name
        """
        if not self.es_client.indices.exists(index=self.db_name):
            self.log.info('Create index %s', self.db_name)
            self.es_client.indices.create(index=self.db_name, body=self.settings)
        else:
            self.log.info('Index %s is exists, no need to create', self.db_name)

    def delete_item(self, item_id):
        """
        Delete item by id
        :param item_id:
        :return:
        """
        self.es_client.delete(index=self.db_name,
                              id=item_id)
        self.refresh()

    def get_item(self, item_id):
        try:
            item = self.es_client.get(index=self.db_name,
                                      id=item_id)
            return item['_source']
        except NotFoundError:
            self.log.warning('Item %s not found in index %s', item_id, self.db_name)
            return None

    def get_items(self, item_ids):
        try:
            res = self.es_client.mget(index=self.db_name,
                                      body={'ids': item_ids},
                                      request_timeout=REQUEST_TIMEOUT)
            return [item.get('_source') for item in res['docs']]
        except NotFoundError:
            self.log.warning('Item %s not found in index %s', item_ids, self.db_name)
            return None

    def insert_item(self, item):
        if 'id' not in item:
            raise RuntimeError('id is missing.')

        # always store indexed time in item
        if 'indexed' not in item:
            item['indexed'] = round(time.time() * 1000)

        self.es_client.index(index=self.db_name,
                             id=item['id'],
                             body=item)
        self.refresh()

    def insert_items(self, items, refresh=False, batch_size=1000):
        """
        Bulk index items. refresh = True if wan tto make items searchable immediately
        """
        body = ''
        res = {}
        current_time = round(time.time() * 1000)
        for cnt, item in enumerate(items, start=1):
            # always store indexed time in item
            if 'indexed' not in item:
                item['indexed'] = current_time
            body += '{"index": {"_id": "%s"}}\n' % item['id']
            body += json.dumps(item) + '\n'
            if cnt % batch_size == 0 or cnt == len(items):
                self.bulk(bulk_body=body, refresh=refresh)
                body = ''

        return res

    def bulk(self, bulk_body, refresh=True):
        res = self.es_client.bulk(
            index=self.db_name,
            body=bulk_body,
            request_timeout=REQUEST_TIMEOUT)
        if refresh:
            self.refresh()
        return res

    def iterate_items(self):
        """
        Return iterator of all items in db
        """
        query = {
            'query': {'match_all': {}},
            'size': 100
        }
        for r in self._scroll_items(query):
            yield r

    def query_items(self, q=None, sort=None, start=0, size=100):
        if q is None or q == '*':
            query = {'match_all': {}}
        else:
            query = {'query_string': {'query': q}}

        dsl_query = {
            'query': query,
            'size': size,
            'from': start,
            'track_total_hits': True,
        }
        if sort is not None:
            dsl_query['sort'] = sort

        res = self.es_client.search(index=self.db_name,
                                    body=dsl_query)
        results = []
        total = res.get('hits', {}).get('total')['value']
        for hit in res.get('hits', {}).get('hits', {}):
            results.append(hit['_source'])

        return total, results

    def facets(self, field_name, q=None, size=100, sort_key=False):
        """
        Aggregate by term with simple query filter
        """
        if q is None or q == '*':
            query = {'match_all': {}}
        else:
            query = {'query_string': {'query': q}}

        dsl_query = {
            'query': query,
            'size': 0,
            'aggs': {
                field_name: {
                    'terms': {
                        'field': field_name,
                        'size': size
                    }
                }
            }
        }
        if sort_key:
            dsl_query['aggs'][field_name]['terms']['order'] = {'_key': 'asc'}

        res = self.es_client.search(index=self.db_name,
                                    body=dsl_query)
        results = []
        for agg in res.get('aggregations').get(field_name, {}).get('buckets'):
            results.append(
                {
                    'key': agg['key'],
                    'count': agg['doc_count']
                }
            )

        return results

    def iterate_random_items(self, dsl_query=None, size=1000):
        if dsl_query is None:
            dsl_query = {'match_all': {}}
        dsl_query = {
            "size": size,
            "query": {
                "function_score": {
                    "random_score": {},
                    "query": dsl_query
                }
            }
        }
        res = self.es_client.search(index=self.db_name,
                                    body=dsl_query)
        for hit in res.get('hits', {}).get('hits', {}):
            yield hit['_source']

    def iterate_query_items(self, q=None, sort=None, max_size=None):
        if q is None or q.strip() == '*':
            query = {'match_all': {}}
        else:
            query = {'query_string': {'query': q}}

        dsl_query = {
            'query': query,
            'size': 100
        }
        if sort is not None:
            dsl_query['sort'] = sort
        # use scroll to get all items
        cnt = 0
        for r in self._scroll_items(dsl_query, max_size):
            cnt += 1
            yield r
            if max_size is not None and cnt > max_size:
                self.log.info('Reach to max_size: %s', max_size)
                break

    def _scroll_items(self, dsl_query, max_size=None):
        """
        Return iterator of all items in db
        """
        res = self.es_client.search(index=self.db_name,
                                    body=dsl_query,
                                    scroll=SCROLL_SIZE)
        num_items = res.get('hits', {}).get('total', {}).get('value')
        self.log.info('Start iterate through %s items in %s...', num_items, self.db_name)
        cnt = 0
        for hit in res.get('hits', {}).get('hits', {}):
            cnt += 1
            yield hit['_source']

        scroll_id = res.get('_scroll_id')
        has_next = True
        while has_next:
            has_next = False
            res = self.es_client.scroll(body={'scroll_id': scroll_id}, scroll=SCROLL_SIZE)
            for hit in res.get('hits', {}).get('hits', {}):
                has_next = True
                cnt += 1
                yield hit['_source']
                if max_size is not None and cnt > max_size:
                    has_next = False
                    self.log.info('Reach to max_size: %s', max_size)
                    break
            scroll_id = res.get('_scroll_id')

    def size(self):
        return self.es_client.count(index=self.db_name).get('count')

    def count(self, query=None):
        if query is None or query == '*':
            return self.size()
        else:
            dsl_query = {
                'query': {'query_string': {'query': query}}

            }
            return self.es_client.count(index=self.db_name, body=dsl_query).get('count')

    def refresh(self):
        self.es_client.indices.refresh(index=self.db_name, request_timeout=REQUEST_TIMEOUT)


def copy_db(src_client, dest_client, src_db, dest_db):
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    log.info('Copy from %s to %s', src_db, dest_db)

    # get settings
    settings = src_client.indices.get_settings().get(src_db)
    if settings is None:
        log.error('Cannot get settings for index %s', src_db)
        return
    # delete unnecessary fields
    for field in ['creation_date', 'provided_name', 'uuid', 'version']:
        del settings['settings']['index'][field]
    log.info('settings:\n%s', json.dumps(settings, indent=2))

    # get mappings
    mappings = src_client.indices.get_mapping().get(src_db)
    if mappings is None:
        log.error('Cannot get mappings for index %s', src_db)
        return
    log.info('mappings:\n%s', json.dumps(mappings, indent=2))

    settings_body = {
        'settings': settings['settings'],
        'mappings': mappings['mappings']
    }
    src_es = ESDB(src_client, src_db)
    dest_es = ESDB(dest_client, dest_db, settings=settings_body)
    # start copy batch by batch
    batch = []
    cnt = 0
    for item in src_es.iterate_items():
        batch.append(item)
        if len(batch) >= 1000:
            cnt += len(batch)
            dest_es.insert_items(batch)
            log.info('Copied %s', cnt)
            batch = []

    if len(batch) > 0:
        cnt += len(batch)
        dest_es.insert_items(batch)

    log.info('Total copied %s', cnt)
