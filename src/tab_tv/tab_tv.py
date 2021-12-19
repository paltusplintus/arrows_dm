import ipyvuetify as v
import ipywidgets as w
from neointerface import NeoInterface
from src.neo_utils import get_table
import pandas as pd
import re
import base64
import qgrid


class TabTabularView(v.Container):
    def __init__(self, parent, neo: NeoInterface = None, qgrid_mode=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluid = True
        self.parent = parent
        self.neo = neo
        self.select = v.Autocomplete(
            items=[],
            hint="Select data",
            multiple=True,
            chips=True,
            v_model=""
        )
        self.select.on_event("change", self.on_select_changed)
        # self.select = w.SelectMultiple(
        #     options = [],
        #     value = [],
        # )
        # self.select.observe(self.on_select_changed2, names='value')

        self.df = pd.DataFrame()
        self.qgrid_mode = qgrid_mode
        self.dt = v.DataTable(disable_filtering=False)
        self.qgw = qgrid.show_grid(pd.DataFrame(),
                                   grid_options={
                                       'editable': False,
                                       'forceFitColumns': False
                                   },
                                   show_toolbar=False,
                                   precision=2
                                   )
        self.btn_download = v.Btn(children=["Create download link"])
        self.btn_download.on_event('click', self.on_btn_download_clicked)
        self.cont_donwload = v.Container()
        self.children = [
            v.Row(children = [
                v.Col(children=[self.select]),
                v.Col(),
            ]),
            (self.qgw if self.qgrid_mode else self.dt),
            self.btn_download,
            self.cont_donwload
        ]

    @staticmethod
    def reverse_regex(regex: str):
        regex = regex[::-1]
        for pair in [
            [r'(.)\\', r'\\\1'],  # anything followed by a \ replaced same preceeded with a \
            [r'(?<!\\)\)', '~('],  # temporarily \) replacing with ~( (unless preceeded with a \
            [r'(?<!(\\)|(\~))\(', ')'],  # a ( unless preceeded with a \ or ~ replaced with )
            [r'\~\(', '('],  # reverse ~( to (
            ['\?\*\.', '.*?'],  # reversing ?*. back to .*?
            ['\*\.', '.*'],  # reversing *. back to .*
            ['\?\+\.', '.+?'],  # reversing ?+. back to .+?
            ['\+\.', '.+'],  # reversing +. back to .+
            ['\^', '$'],
            ['\$', '^'],
        ]:
            # regex = regex.replace(pair[0], pair[1])
            regex = re.sub(pair[0], pair[1], regex)
        return regex

    def _helper_get_table(self):
        labels, where = [], []
        for i, item in enumerate(self.select.v_model):
            if i == 0:
                labels.append(item)
            else:
                regex0 = r'\(\:\`(.*?)\`\)$'
                regex1 = self.reverse_regex(regex0)
                #lbl = re.findall(r'^\)\`(.*?)\`\:\(', item[::-1])[0][::-1]
                lbl = re.findall(regex1, item[::-1])[0][::-1]
                #lbl.replace(':','`:`') #in case of multiple labels adding ` ` around : to support spaces in labels
                regex2 = r'^\(\:\`' + labels[-1] + r'\`\)'
                repl1 = f"(x{str(len(labels))})"
                item = re.sub(regex2, repl1, item)
                item = re.sub(r'^\)\`(.*?)\`\:\(', f"){str(len(labels) + 1)}x(", item[::-1])[::-1]
                where.append(item)
                labels.append(lbl)
        return labels, where

    def on_select_changed(self, widget, event, data):
        if self.neo:
            labels, where = self._helper_get_table()
            items = [res['all'] for res in get_table(neo=self.neo, labels=labels, where=where)]
            self.df = pd.DataFrame(items)
            self.df = self.df[sorted(self.df.columns)]
            if self.qgrid_mode:
                self.qgw.df = self.df
            else:
                self.dt.headers = [{'text': col, 'value': col} for col in self.df.columns]
                self.dt.items = items
            self.refresh_select()
        self.cont_donwload.children = []

    # def on_select_changed2(self, widget):
    #     print(widget)

    def set_connection(self, neo: NeoInterface):
        self.neo = neo

    def refresh_select(self):
        if self.neo:
            if self.select.v_model:
                cur_select = self.select.v_model
                if len(cur_select) == 1:
                    last_label = cur_select[-1]
                else:
                    regex0 = r'\(\:\`(.*?)\`\)$'
                    regex1 = self.reverse_regex(regex0)
                    last_label = re.findall(regex1, cur_select[-1][::-1])[0][::-1]
                labels, where = self._helper_get_table()
                q = get_table(neo=self.neo, labels=labels, where=where, return_query_only=True)
                q1 = "\n".join(q.splitlines()[:-3])
                q1 += f" WITH * MATCH (x{len(labels)})-[r]->(new) RETURN DISTINCT type(r), labels(new)"
                res1 = self.neo.query(q1)
                items_fwrd = [f"(:`{last_label}`)-[:`{r['type(r)']}`]->(:`{'`:`'.join(r['labels(new)'])}`)"
                              for r in res1]
                q2 = "\n".join(q.splitlines()[:-3])
                q2 += f" WITH * MATCH (x{len(labels)})<-[r]-(new) RETURN DISTINCT type(r), labels(new)"
                res1 = self.neo.query(q2)
                items_bwrd = [f"(:`{last_label}`)<-[:`{r['type(r)']}`]-(:`{'`:`'.join(r['labels(new)'])}`)"
                              for r in res1]
                self.select.items = cur_select + items_fwrd + items_bwrd
            else:
                opts = [label for label in self.neo.get_labels() if label not in ["_File_", "_MergeOn_", "_Metadata_"]]
                if opts:
                    self.select.items = opts

    @staticmethod
    def create_download_link(df, title="Download CSV file", filename="data.csv"):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode())
        payload = b64.decode()
        html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
        html = html.format(payload=payload, title=title, filename=filename)
        return w.HTML(html)

    def on_btn_download_clicked(self, widget, event, data):
        self.cont_donwload.children = [
            self.create_download_link(df=self.df)
        ]

    def render(self):
        self.refresh_select()
