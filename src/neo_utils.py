from neointerface import NeoInterface
import json
import re


def get_loaded_files(neo: NeoInterface):
    q = """
    MATCH (f:_File_:_Metadata_)
    RETURN f.filename as filename
    """
    params = {}
    res = neo.query(q, params)
    return [r['filename'] for r in res]


def load_content(neo: NeoInterface, filename: str, content: str):
    # #loading metadata
    ext = filename.split(".")[-1]
    q = f"""         
    MERGE (f:_File_:_Metadata_{{filename: $filename}})
    SET f.{ext} = $content
    WITH *
    MATCH (f_last:_File_:_Metadata_) 
    WHERE
        f_last <> f
    AND 
        NOT EXISTS ( (f_last)-[:NEXT]->(:_File_:_Metadata_) )
    MERGE (f_last)-[:NEXT]->(f)
    """
    params = {'filename': filename, 'content': content}
    res = neo.query(q, params)
    return res


def extract_jsons(neo: NeoInterface, merge_on: dict = None):
    if merge_on is None:
        merge_on = {}
    q = """
    MATCH path=(f1:_File_:_Metadata_)-[:NEXT*0..1000]->(f2:_File_:_Metadata_)
    WHERE 
        NOT EXISTS ( (:_File_:_Metadata_)-[:NEXT]->(f1) )
    AND
        NOT EXISTS ( (f2)-[:NEXT]->(:_File_:_Metadata_) )
    WITH nodes(path) as nds
    UNWIND nds as nd
    CALL apoc.do.when(
        nd.filename ENDS WITH 'json'
        ,
        'CALL custom.load_arrows(nd.json, $mergeOn) YIELD node_map, rel_map RETURN *'
        ,
        'CALL custom.load_csv_string(nd.csv, nd.filename, $mergeOn) YIELD node RETURN *'
        ,
        {nd: nd, mergeOn: $mergeOn}
    ) YIELD value
    RETURN *
    """
    params = {'mergeOn': merge_on}
    res = neo.query(q, params)
    return res


def delete_content(neo: NeoInterface, names: list):
    q = """
    MATCH (f1:_File_:_Metadata_)
    WHERE f1.filename in $names
    OPTIONAL MATCH (f0:_File_:_Metadata_)-[:NEXT]->(f1)-[:NEXT]->(f2:_File_:_Metadata_)
    CALL apoc.do.when(
        NOT (f0 IS NULL OR f2 IS NULL),
        'MERGE (f0)-[:NEXT]->(f2) RETURN f0, f2',
        'RETURN f0, f2',
        {f0:f0, f2:f2}
    ) YIELD value
    DETACH DELETE f1
    RETURN f0, f2    
    """
    params = {'names': names}
    res = neo.query(q, params)
    return res


def get_file_content(neo: NeoInterface, filename: str):
    q = """
    MATCH (f:_File_:_Metadata_)
    WHERE f.filename = $filename
    RETURN f.json as content
    """
    params = {'filename': filename}
    res = neo.query(q, params)
    return res


def get_files_list(neo: NeoInterface):
    q = """
    MATCH path = (f:_File_:_Metadata_)-[:NEXT*0..1000]->(f1:_File_:_Metadata_)
    WHERE
        (NOT EXISTS ( (:_File_:_Metadata_)-[:NEXT]->(f) ))
    AND
        (NOT EXISTS ( (f1)-[:NEXT]->(:_File_:_Metadata_) ))
    RETURN [x in nodes(path) | x.filename] as filenames
    """
    res = neo.query(q)

    return res


def get_files_stats(neo: NeoInterface, filenames: list, detailed=False):
    if detailed:
        q_return = "RETURN nodes"
    else:
        q_return = "RETURN nodes['labels'] as nodes, count(nodes) as count"

    q = f"""
    MATCH (f:_File_:_Metadata_)
    WHERE f.filename in $filenames
    WITH apoc.convert.fromJsonMap(f.json) as map
    WITH map
    UNWIND map['nodes'] as nd
    WITH map, nd, apoc.map.submap(nd, ['labels', 'properties']) as nodes
    {q_return}        
    """
    params = {'filenames': filenames}
    res = neo.query(q, params)
    return res


def get_arrows_json(neo: NeoInterface, where=None, incl_neighbors=False, limit=None, step=500):
    assert where is None or isinstance(where, str)
    assert isinstance(incl_neighbors, bool)
    assert limit is None or isinstance(limit, int)
    assert isinstance(step, int)
    assert step > 0
    q_limit = ("WITH * LIMIT " + str(limit) if limit else "")
    q_where = (f"WHERE {where}" if where else "")
    q_opt_where = (
        "" if incl_neighbors else "WHERE size(apoc.coll.disjunction(labels(x), labels(y))) = 0")  # TODO: change to perm solution - this is temp
    # if incl_neighbors:
    q = f"""
        MATCH (x)
        {q_where}   
        OPTIONAL MATCH path = (x)-[r]-(y)
        {q_opt_where}                         
        {q_limit}
        WITH *
        ORDER BY id(x), id(y), id(r) 
        WITH 
            apoc.coll.toSet(collect(distinct x) + collect(distinct y)) as nds, 
            collect(distinct r) as rls  
        WITH 
        [x in nds | 
            {{		
                id: "n" + toString(id(x)),
                labels: labels(x), 
                properties:x{{.*}},
                caption:"",
                style: {{}}
            }}
        ] as nds, 
        [r in [y in rls WHERE NOT y IS NULL] |
            {{
                id: "r" + toString(id(r)),
                type: type(r),
                style: {{}},
                properties: r{{.*}},
                fromId: "n" + toString(id(startNode(r))),
                toId: "n" + toString(id(endNode(r)))
            }}
        ] as rls
        WITH *, size(nds) as sz, 200 as step
        WITH *, toInteger(ceil(sqrt(sz))) as axlen
        WITH *, apoc.coll.flatten([x in range(1, axlen) | [y in range(1, axlen) | {{position: {{x:(-axlen/2+x)*step, y:(-axlen/2+y)*step}}}}]][0..apoc.coll.max([sz-1,1])]) as positions
        WITH *, [pair in apoc.coll.zip(nds,positions) | apoc.map.merge(pair[0],pair[1])] as nds, rls
        RETURN 
            nds as nodes, 
            rls as relationships, 
            {{}} as style
        """
    res = neo.query(q)

    return res


def get_table(neo: NeoInterface, labels=None, where=None, limit=None, return_query_only=False,
              allow_same_label_twice=True):
    assert labels is None or isinstance(labels, list) or isinstance(labels, str)
    assert where is None or isinstance(where, str) or isinstance(where, list)
    assert limit is None or isinstance(limit, int)
    assert isinstance(return_query_only, bool)
    if labels:
        if isinstance(labels, str):
            labels = [labels]
        q_limit = ("WITH * LIMIT " + str(limit) if limit else "")
        q_match_add = []
        if where:
            if isinstance(where, str):
                q_where = f"WITH * WHERE {where}"
            elif isinstance(where, list):
                mod_where = []
                for wh in where:
                    # transferring where conditions on relationship btw 2 classes to MATCH statement
                    if re.match(r'\(x\d+\)<?-\[\:`?.+?`?\]->?\(x\d+?\)', wh):
                        q_match_add.append(wh)
                    else:
                        mod_where.append(wh)
                where = mod_where
                if where:
                    q_where = f"WITH * WHERE {' AND '.join(where)}"
                else:
                    q_where = ""
        else:
            q_where = ""
        q_match, q_with, q_return = [], [], []
        for i, label in enumerate(labels):
            v = "x" + str(i + 1)
            q_match.append(f"({v}:`{label}`)")
            if allow_same_label_twice:
                q_with.append(
                    f"apoc.map.fromPairs([k in keys({v}) | ['{str(i + 1)}_{label}' + '.' + k, {v}[k]]]) as {v}")
            else:
                q_with.append(f"apoc.map.fromPairs([k in keys({v}) | ['{label}' + '.' + k, {v}[k]]]) as {v}")
            q_return.append(v)
        q = f"""
            MATCH {", ".join(q_match + q_match_add)}                
            {q_where}  
            {q_limit}
            WITH {", ".join(q_with)}
            RETURN apoc.map.mergeList([{", ".join(q_return)}]) as all
            """
        if return_query_only:
            return q
        else:
            res = neo.query(q)
            return res
    else:
        return []


def get_label_properties(neo: NeoInterface):
    q = f"""   
    CALL db.schema.nodeTypeProperties() YIELD nodeLabels, propertyName
    UNWIND nodeLabels as label
    WITH label, collect(propertyName) as properties         
    RETURN apoc.map.fromPairs(collect([label, properties])) as map
    """
    res = neo.query(q)
    return res


def save_merge_on(neo: NeoInterface, label: str, properties: str):
    q = """   
        MERGE (m:_MergeOn_:_Metadata_{label:$label})
        SET m.properties = $properties
        """
    params = {'label': label, 'properties': properties}
    res = neo.query(q, params)
    return res


def delete_merge_on(neo: NeoInterface, label: str):
    q = """   
        MATCH (m:_MergeOn_:_Metadata_{label:$label})
        DETACH DELETE m
        """
    params = {'label': label}
    res = neo.query(q, params)
    return res


def get_merge_on(neo: NeoInterface):
    q = """   
        MATCH (m:_MergeOn_:_Metadata_)
        RETURN apoc.map.fromPairs(collect([m.label, m.properties])) as map                 
        """
    res = neo.query(q)
    return res


# #--------------------------------------------- #


def setup_custom_apoc_proc(neo: NeoInterface):
    q = """
    call apoc.custom.asProcedure(
    "load_arrows", 
    "
    WITH apoc.convert.fromJsonMap($json) as map
    UNWIND map['nodes'] as nd
    WITH *, apoc.coll.intersection(nd['labels'], keys($mergeOn)) as hc_labels // list of relevant labels from the merge_on map
    WITH *, apoc.coll.toSet(apoc.coll.flatten(apoc.map.values($mergeOn, hc_labels))) as hc_props // list of relevant properties 
    WITH *, [prop in hc_props WHERE prop in keys(nd['properties'])] as hc_props // filter to keep only the existing ones
    WITH 
        *,
        CASE WHEN size(nd['labels']) = 0 THEN 
            ['No Label']
        ELSE
            nd['labels']
        END as labels,
        CASE WHEN size(hc_props) > 0 THEN 
            {
                identProps: 
                    CASE WHEN size(apoc.coll.intersection(keys(nd['properties']), hc_props)) = 0 and nd['caption'] <> '' THEN 
                        {value: nd['caption']}
                    ELSE
                        apoc.map.submap(nd['properties'], hc_props)
                    END
                ,
                onMatchProps: apoc.map.submap(nd['properties'], [key in keys(nd['properties']) 
                                                                 WHERE NOT key IN hc_props])
            }
        ELSE
            {
                identProps:     
                    CASE WHEN size(keys(nd['properties'])) = 0 and nd['caption'] <> '' THEN 
                        {value: nd['caption']}
                    ELSE
                        nd['properties']
                    END
                ,
                onMatchProps: {}
            }                   
        END as props                        
    WITH 
        map,
        nd,
        labels,
	props['identProps'] as identProps,
	props['onMatchProps'] as onMatchProps,
	props['onMatchProps'] as onCreateProps //TODO: change if these need to differ in the future     
    CALL apoc.merge.node(labels, identProps, onMatchProps, onMatchProps)
    YIELD node 
    WITH map, apoc.map.fromPairs(collect([nd['id'], node])) as node_map
    UNWIND map['relationships'] as rel
    call apoc.merge.relationship(
        node_map[rel['fromId']], 
        CASE WHEN rel['type'] = '' OR rel['type'] IS NULL THEN 'RELATED' ELSE rel['type'] END, 
        rel['properties'], 
        {}, 
        node_map[rel['toId']], {}
    )
    YIELD rel as relationship
    WITH node_map, apoc.map.fromPairs(collect([rel['id'], relationship])) as rel_map
    RETURN node_map, rel_map
    ", 
    "write", 
    [['node_map','MAP'],['rel_map','MAP']], 
    [['json','STRING'],['mergeOn','MAP']],
    'Loads json content from Arrows.app into Neo4j database by merging all nodes separately on all their prorties and merging relationships. In case mergeOn parameter is not an empty map, then merges on the specified properties')
    """
    params = {}
    res = neo.query(q, params)
    return res

def setup_custom_apoc_proc2(neo: NeoInterface):
    q = """
    call apoc.custom.asProcedure(
    "load_csv_string", 
    "        
        WITH    
            *,
            [apoc.text.join(apoc.text.split($label, '\.')[..-1], '\.')] as labels,     
            apoc.text.split($csv, '\n') as coll
        WITH *, labels, coll[0] as props, coll[1..] as data
        WITH *, labels, apoc.text.split(props, ',') as props, [x in data | apoc.text.split(x, ',')] as data
        UNWIND data as row
        WITH *, labels, apoc.map.fromPairs(apoc.coll.zip(props, row)) as data
        
        WITH *, labels, data, apoc.coll.intersection(labels, keys($mergeOn)) as hc_labels
        WITH *, apoc.coll.toSet(apoc.coll.flatten(apoc.map.values($mergeOn, hc_labels))) as hc_props
        WITH *, [prop in hc_props WHERE prop in keys(data)] as hc_props
        WITH *,
            CASE WHEN size(hc_props) > 0 THEN 
                {
                    identProps: apoc.map.submap(data, hc_props)
                    ,
                    onMatchProps: apoc.map.submap(data, [key in keys(data) WHERE NOT key IN hc_props])
                }
            ELSE
                {
                    identProps: data,                      
                    onMatchProps: {}
                }
            END as props 
        WITH 
            labels,
            data,
            props['identProps'] as identProps,
            props['onMatchProps'] as onMatchProps,
            props['onMatchProps'] as onCreateProps 
        CALL apoc.merge.node(labels, identProps, onMatchProps, onMatchProps)
        YIELD node
        RETURN node 
    ", 
    "write", 
    [['node','NODE']], 
    [['csv','STRING'], ['label','STRING'], ['mergeOn','MAP']],
    'Loads csv content into Neo4j database by merging all nodes separately on all their properties. In case mergeOn parameter is not an empty map, then merges on the specified properties')
    """
    params = {}
    res = neo.query(q, params)
    return res
