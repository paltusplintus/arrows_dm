from neointerface import NeoInterface


def test_custom_load_arrows():
    neo = NeoInterface()
    neo.clean_slate()
    neo.query("CREATE (p:Person{name:'Frank'})")
    q = """
    CALL custom.load_arrows($json, $mergeOn) YIELD node_map, rel_map
    RETURN *
    """
    json_str = """
    {
  "nodes": [
    {
      "id": "n0",
      "position": {
        "x": -171.99999999999997,
        "y": 3
      },
      "caption": "",
      "labels": [
        "Job"
      ],
      "properties": {
        "id": "123"
      },
      "style": {}
    },
    {
      "id": "n1",
      "position": {
        "x": 75,
        "y": 250
      },
      "caption": "",
      "labels": [
        "Person"
      ],
      "properties": {
        "name": "Frank",
        "age": "30"
      },
      "style": {}
    }
  ],
  "relationships": [
    {
      "id": "n0",
      "fromId": "n1",
      "toId": "n0",
      "type": "DOES",
      "properties": {},
      "style": {}
    }
  ],
  "style": {
    "font-family": "sans-serif",
    "background-color": "#ffffff",
    "node-color": "#ffffff",
    "border-width": 4,
    "border-color": "#000000",
    "radius": 50,
    "node-padding": 5,
    "node-margin": 2,
    "outside-position": "auto",
    "node-icon-image": "",
    "node-background-image": "",
    "icon-position": "inside",
    "icon-size": 64,
    "caption-position": "inside",
    "caption-max-width": 200,
    "caption-color": "#000000",
    "caption-font-size": 50,
    "caption-font-weight": "normal",
    "label-position": "inside",
    "label-display": "pill",
    "label-color": "#000000",
    "label-background-color": "#ffffff",
    "label-border-color": "#000000",
    "label-border-width": 4,
    "label-font-size": 40,
    "label-padding": 5,
    "label-margin": 4,
    "directionality": "directed",
    "detail-position": "inline",
    "detail-orientation": "parallel",
    "arrow-width": 5,
    "arrow-color": "#000000",
    "margin-start": 5,
    "margin-end": 5,
    "margin-peer": 20,
    "attachment-start": "normal",
    "attachment-end": "normal",
    "relationship-icon-image": "",
    "type-color": "#000000",
    "type-background-color": "#ffffff",
    "type-border-color": "#000000",
    "type-border-width": 0,
    "type-font-size": 16,
    "type-padding": 5,
    "property-position": "outside",
    "property-alignment": "colon",
    "property-color": "#000000",
    "property-font-size": 16,
    "property-font-weight": "normal"
  }
}
    """
    params = {'json': json_str, 'mergeOn': {'Person': ['name']}}
    res = neo.query(q, params)
    assert res == [
        {'node_map': {
            'n0': {'id': '123'},
            'n1': {'name': 'Frank', 'age': '30'}
        },
         'rel_map': {
             'n0': ({'name': 'Frank', 'age': '30'}, 'DOES', {'id': '123'})}
        }
    ]

#no label/type/properties on nodes/relationships
def test_custom_load_arrows_captions():
    neo = NeoInterface()
    neo.clean_slate()
    q = """
    CALL custom.load_arrows($json, $mergeOn) YIELD node_map, rel_map
    RETURN *
    """
    json_str = """
    {
      "nodes": [
        {
            "id": "n3",     
            "caption": "Alex",
            "style": {},
            "labels": [],
            "properties": {}
        },
        {
            "id": "n4",      
            "caption": "Bob",      
            "labels": [],
            "properties": {}
        }
      ],
        "relationships": [
        {
            "id": "n2",
            "type": "",
            "style": {},
            "properties": {},
            "fromId": "n3",
            "toId": "n4"
        }
        ]      
    }
    """
    params = {'json': json_str, 'mergeOn': {}}
    res0 = neo.query(q, params)

    res = neo.query("MATCH (x:`No Label`{value: 'Alex'})-[r:RELATED]->(y:`No Label`{value: 'Bob'}) RETURN *")
    assert len(res) == 1