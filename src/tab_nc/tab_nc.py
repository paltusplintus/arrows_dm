import os
import ipyvuetify as v
import ipywidgets as w
from neointerface import NeoInterface


class TabNeoConnection(v.Container):
    def __init__(self, parent, neo: NeoInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluid = True
        self.parent = parent
        self.neo = neo
        self.neo4j_host = v.TextField(v_model=os.environ.get("NEO4J_HOST"), hint="Neo4j host", persistent_hint=True)
        self.neo4j_user = v.TextField(v_model=os.environ.get("NEO4J_USER"))
        self.neo4j_password = w.Password(value=os.environ.get("NEO4J_PASSWORD"))
        self.btn_connect = v.Btn(children=["Connect"])
        self.btn_connect.on_event('click', self.on_btn_connect_clicked)
        self.out = w.Output()
        self.btn_cleardb = v.Btn(children=["Clear Database"])
        self.btn_cleardb.on_event('click', self.on_btn_cleardb_clicked)
        self.children = [
            self.neo4j_host,
            self.neo4j_user,
            self.neo4j_password,
            self.btn_connect,
            self.out,
            self.btn_cleardb
        ]
        self.render()

    def on_btn_connect_clicked(self, widget, event, data):
        # try:
        self.neo = NeoInterface(
            host=self.neo4j_host.v_model,
            credentials=(self.neo4j_user.v_model, self.neo4j_password.value),
            verbose=False
        )
        self.parent.set_connection(self.neo)
        self.out.clear_output()
        with self.out:
            print(f"Connection with {self.neo4j_host.v_model} established")
            print(f"Nodes: {self.neo.query('MATCH (x) RETURN count(x)')[0]['count(x)']}")
#         except:
#             self.out.clear_output()
#             with self.out:
#                 print("""
# Could not establish connection.
# Please that check hosts are correct and accessible via network and that the credentials provided are correct
#                 """)
        if self.neo:
            self.parent.render()

    def on_btn_cleardb_clicked(self, widget, event, data):
        self.neo.clean_slate()
        self.out.clear_output()
        with self.out:
            print(f"Nodes: {self.neo.query('MATCH (x) RETURN count(x)')[0]['count(x)']}")

    def render(self):
        pass
