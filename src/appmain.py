import ipyvuetify as v
from neointerface import NeoInterface
from src.tab_am.tab_am import TabArrowsManager
from src.tab_nc.tab_nc import TabNeoConnection
from src.tab_tv.tab_tv import TabTabularView


class AppTabs(v.Tabs):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tab_am_title = v.Tab(children=["Arrows Manager"])
        self.tab_am_title.on_event('change', self.on_tab_am_title_activated)
        self.tab_am = TabArrowsManager(parent=self)

        self.tab_tv_title = v.Tab(children=["Tabular View"])
        self.tab_tv_title.on_event('change', self.on_tab_tv_title_activated)
        self.tab_tv = TabTabularView(parent=self)

        self.tab_nc_title = v.Tab(children=["Setup Neo4j connection"])
        self.tab_nc_title.on_event('change', self.on_tab_nc_title_activated)
        self.tab_nc = TabNeoConnection(parent=self)

        self.all_tabs = [
            self.tab_am_title,
            v.TabItem(children=[self.tab_am]),
            self.tab_tv_title,
            v.TabItem(children=[self.tab_tv]),
            self.tab_nc_title,
            v.TabItem(children=[self.tab_nc]),
        ]
        self.children = self.all_tabs

        self.tab_nc.on_btn_connect_clicked(None, None, None)

    def set_connection(self, neo: NeoInterface):
        self.neo = neo
        self.tab_am.set_connection(neo)
        self.tab_tv.set_connection(neo)

    def on_tab_am_title_activated(self, widget, event, data):
        self.tab_am.render()

    def on_tab_nc_title_activated(self, widget, event, data):
        self.tab_nc.render()

    def on_tab_tv_title_activated(self, widget, event, data):
        self.tab_tv.render()

    def render(self):
        self.tab_am.render()
