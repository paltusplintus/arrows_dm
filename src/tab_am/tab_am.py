import ipyvuetify as v
from neointerface import NeoInterface
from src.tab_am.col_json import ColJson
from src.tab_am.col_preview import ColPreview
from src.neo_utils import setup_custom_apoc_proc, setup_custom_apoc_proc2


class TabArrowsManager(v.Container):
    def __init__(self, parent, neo: NeoInterface = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluid = True
        self.parent = parent
        self.neo = neo
        self.col_json = ColJson(parent=self)
        self.col_preview = ColPreview(parent=self)
        self.children = [
            v.Row(children=[
                self.col_json,
                self.col_preview,
            ],
                fluid=True)
        ]
        self.render()

    def get_merge_on(self):
        dct_merge_on = {}
        if 'merge_on' in self.col_preview.__dict__:
            dct_merge_on = self.col_preview.merge_on
        return dct_merge_on

    def set_connection(self, neo: NeoInterface):
        self.neo = neo
        self.col_json.neo = self.parent.neo
        self.col_preview.neo = self.parent.neo
        if self.neo:
            setup_custom_apoc_proc(self.neo)
            setup_custom_apoc_proc2(self.neo)

    def render(self):
        self.col_preview.render()
