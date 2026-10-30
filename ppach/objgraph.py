"""Flatten the game's serialized object graph.

Both Options.jopt (JSON) and decoded .zsav saves store objects as
{"Contents": {"Objects": [{"ObjectID": n, "ObjectValue": ...}, ...]}}.
References are {"ObjectID": n}; collections are {"CollectionValues": [...]}
and dictionaries are collections of {"Key", "Value"} pairs. Fields starting
with '#' are type bookkeeping.
"""


def objects(doc, section='Contents'):
    return {o['ObjectID']: o for o in doc[section]['Objects']}


def resolver(objs, max_depth=60):
    def res(v, depth=0):
        if depth > max_depth:
            return '...'
        if isinstance(v, dict):
            if set(v) == {'ObjectID'}:
                o = objs.get(v['ObjectID'])
                return res(o.get('ObjectValue'), depth + 1) if o else v
            if 'CollectionValues' in v:
                cv = v['CollectionValues'] or []
                if cv and isinstance(cv[0], dict) and 'Key' in cv[0]:
                    return {str(res(x['Key'], depth + 1)): res(x.get('Value'), depth + 1)
                            for x in cv}
                return [res(x, depth + 1) for x in cv]
            keys = [k for k in v if not k.startswith('#')]
            if keys == ['Value'] or keys == ['BoxedValue']:
                return res(v[keys[0]], depth + 1)
            return {k: res(x, depth + 1) for k, x in v.items() if not k.startswith('#')}
        if isinstance(v, list):
            return [res(x, depth + 1) for x in v]
        return v
    return res


def top_level(doc, section='Contents'):
    objs = objects(doc, section)
    top = [o for o in objs.values() if o.get('TopLevel')][0]
    return resolver(objs)(top['ObjectValue'])


def guid(v):
    return v.get('SerializationGuid') if isinstance(v, dict) else None
