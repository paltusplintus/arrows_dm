import json
import ipyvuetify as v
import ipywidgets as w
from src.neo_utils import delete_content, extract_jsons, get_file_content, get_files_list, get_files_stats, \
    get_arrows_json, get_label_properties, save_merge_on, delete_merge_on, get_merge_on
import pprint


class ColPreview(v.Col):
    TEXTFIELD_PREFIX = "text_field_"

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pp = pprint.PrettyPrinter(indent=1)
        self.parent = parent
        self.neo = None
        self.label_properties = {}
        self.merge_on = {}
        # #files
        self.list_of_chkboxes = []
        self.list_of_selected_files = []
        self.col_list_files = v.Col(children=[])
        self.btn_delete = v.Btn(children=["Delete"], disabled=True)
        self.btn_delete.on_event('click', self.on_btn_delete_clicked)
        self.btn_edit = v.Btn(children=["Edit"], disabled=True)
        self.btn_edit.on_event('click', self.on_btn_edit_clicked)
        self.btn_edit_all = v.Btn(children=["Edit All"])
        self.btn_edit_all.on_event('click', self.on_btn_edit_all_clicked)
        # #summary
        self.chk_detailed_summary = v.Checkbox(label="Detailed Summary", v_model=False, disabled=True)
        self.chk_detailed_summary.on_event("change", self.on_chk_detailed_summary_changed)
        self.out_summary = w.Output()
        # #labels
        self.btn_edit_by_label = v.Btn(children=["Edit"])
        self.btn_edit_by_label.on_event('click', self.on_btn_edit_by_label_clicked)
        self.chk_include_neighbors = v.Checkbox(label="Include Neighbors", v_model=False)
        self.select_edit_selected = v.Autocomplete(items=[], select_first=True, hint='Edit')
        # #setup merge
        self.select_setup_merge_label = v.Autocomplete(items=[], select_first=True, label="Select Label")
        self.select_setup_merge_label.on_event('change', self.on_select_setup_merge_label_changed)
        self.text_setup_merge_label = v.TextField(v_model="", label="Enter other Label")
        self.text_setup_merge_label.on_event('input', self.on_text_setup_merge_label_changed)
        self.text_setup_merge_prop = v.TextField(v_model="", label="Comma-separated property list")
        self.text_setup_merge_prop.on_event('input', self.on_text_setup_merge_prop_changed)
        self.btn_save_merge = v.Btn(children=["Save"])
        self.btn_save_merge.on_event('click', self.on_btn_save_merge_clicked)
        self.btn_delete_merge = v.Btn(children=["Delete"])
        self.btn_delete_merge.on_event('click', self.on_btn_delete_merge_clicked)
        self.out_setup_merge = w.Output()
        # #all
        self.out = w.Output()
        self.children = [
            v.Tabs(children=[
                v.Tab(children=["Files"]),
                v.TabItem(children=[
                    v.Row(children=[
                        v.Col(children=[
                            self.col_list_files,
                            self.btn_delete,
                            self.btn_edit,
                            self.btn_edit_all,
                        ]),
                        v.Col(children=[
                            self.chk_detailed_summary,
                            self.out_summary,
                        ]),
                    ])
                ]),
                v.Tab(children=["Labels"]),
                v.TabItem(children=[
                    v.Row(children=[
                        self.select_edit_selected,
                        self.chk_include_neighbors
                    ]),
                    self.btn_edit_by_label,
                ]),
                v.Tab(children=["Merge_On Setup"]),
                v.TabItem(children=[
                    v.Row(children=[
                        v.Col(children=[
                            self.select_setup_merge_label,
                            self.text_setup_merge_label,
                            self.text_setup_merge_prop,
                            self.btn_save_merge,
                            self.btn_delete_merge,
                        ]),
                        v.Col(children=[
                            self.out_setup_merge,
                        ])
                    ])
                ]),
            ]),
            self.out
        ]
        self.render()

    def on_btn_edit_clicked(self, widget, event, data):
        neores = get_file_content(self.neo, self.list_of_selected_files[0])
        if len(neores) == 1:
            json_content = neores[0]['content']
            if json_content:
                self.parent.col_json.text_area.v_model = json_content
            else:
                self.out.clear_output()
                with self.out:
                    print(
                        "ERROR: selected file does not have content in .json property. Please contact database administrator.")
        elif len(neores) > 1:
            self.out.clear_output()
            with self.out:
                print("ERROR: there is >1 file with specified name. Please contact database administrator.")
        else:
            self.out.clear_output()
            with self.out:
                print(
                    f"ERROR: no file with name {self.list_of_selected_files[0]} was found. Please contact database administrator.")

    def on_btn_edit_all_clicked(self, widget, event, data):
        res = get_arrows_json(neo=self.neo, where="NOT (x:_File_:_Metadata_) and NOT (x:_MergeOn_:_Metadata_)",
                              incl_neighbors=True)
        if res:
            self.parent.col_json.text_area.v_model = json.dumps(res[0])
        else:
            self.out.clear_output()
            with self.out:
                print(
                    f"No data found in the database")

    def on_btn_edit_by_label_clicked(self, widget, event, data):
        if self.select_edit_selected.v_model:
            label = self.select_edit_selected.v_model
            res = get_arrows_json(neo=self.neo, where=f"x:`{label}`", incl_neighbors=self.chk_include_neighbors.v_model)
            if res:
                self.parent.col_json.text_area.v_model = json.dumps(res[0])
            else:
                self.out.clear_output()
                with self.out:
                    print(
                        f"No {label} data found in the database")

    def on_btn_delete_clicked(self, widget, event, data):
        delete_content(self.neo, names=self.list_of_selected_files)
        self.neo.clean_slate(keep_labels=['_File_', '_MergeOn_', '_Metadata_'])
        extract_jsons(neo=self.neo, merge_on=self.parent.get_merge_on())
        self.render()

    def on_chk_detailed_summary_changed(self, widget, event, data):
        self.refresh_selected_files_stats()

    def get_selected_files(self):
        return [item.label for item in self.list_of_chkboxes if item.v_model]

    def on_chkbox_changed(self, widget, event, data):
        self.list_of_selected_files = self.get_selected_files()
        self.refresh_selected_files_stats()
        if len(self.list_of_selected_files) != 1:
            self.btn_edit.disabled = True
        else:
            self.btn_edit.disabled = False
        if len(self.list_of_selected_files) > 0:
            self.chk_detailed_summary.disabled = False
            self.btn_delete.disabled = False
        else:
            self.chk_detailed_summary.disabled = True
            self.btn_delete.disabled = True
        # print(self.list_of_selected_files)

    def refresh_col_list_files(self):
        res = get_files_list(self.neo)
        self.out.clear_output()
        if res:
            with self.out:
                assert len(res) == 1, """
>1 chain of _File_ nodes exists in the database.
Clear your database if you have a backup of you data, otherwise contact the database administrator.  
                """
            files = res[0]['filenames']
            if files:
                self.col_list_files.children = []
                self.list_of_chkboxes = []
                for i, file in enumerate(files):
                    chkbox = v.Checkbox(label=file, v_model=False)
                    self.list_of_chkboxes.append(chkbox)
                    self.list_of_chkboxes[i].on_event("change", self.on_chkbox_changed)
                self.col_list_files.children = self.list_of_chkboxes
            else:
                self.col_list_files.children = []
                self.out.clear_output()
                with self.out:
                    print("No files data was found in the database")
        else:
            self.col_list_files.children = []
            with self.out:
                print("No files data was found in the database or >1000 files")

    def refresh_selected_files_stats(self):
        res = get_files_stats(self.neo, filenames=self.get_selected_files(), detailed=self.chk_detailed_summary.v_model)
        self.out_summary.clear_output()
        if res:
            with self.out_summary:
                self.pp.pprint(res)

    def refresh_select_edit_selected(self):
        self.select_edit_selected.items = [label for label in self.neo.get_labels() if
                                           label not in ['_File_', '_MergeOn_', '_Metadata_']]
        if self.select_edit_selected.items:
            self.select_edit_selected.v_model = self.select_edit_selected.items[0]

    def on_btn_save_merge_clicked(self, widget, event, data):
        label = (self.select_setup_merge_label.v_model
                 if self.select_setup_merge_label.v_model != "Other" else
                 self.text_setup_merge_label.v_model)
        prop_list = self.text_setup_merge_prop.v_model.split(",")
        for prop in prop_list:
            self.neo.create_index(label, prop) #TODO: for Neo4j enterprise edition the can set index on pair of properties
        save_merge_on(
            neo=self.neo,
            label=label,
            properties=self.text_setup_merge_prop.v_model
        )
        self.refresh_out_setup_merge()

    def on_btn_delete_merge_clicked(self, widget, event, data):
        label = (self.select_setup_merge_label.v_model
                 if self.select_setup_merge_label.v_model != "Other" else
                 self.text_setup_merge_label.v_model)
        prop_list = self.text_setup_merge_prop.v_model.split(",")
        for prop in prop_list:
            self.neo.drop_index(f"{label}.{prop}")
        delete_merge_on(
            neo=self.neo,
            label=label
        )
        self.refresh_out_setup_merge()

    def on_select_setup_merge_label_changed(self, widget, event, data):
        cur_selection = self.select_setup_merge_label.v_model
        if cur_selection and cur_selection != 'Other':
            self.text_setup_merge_prop.v_model = self.label_properties[cur_selection]
            self.text_setup_merge_label.disabled = True
            self.btn_save_merge.disabled = False
            self.btn_delete_merge.disabled = False
        else:
            self.text_setup_merge_prop.v_model = ''
            self.text_setup_merge_label.disabled = False
            self.btn_save_merge.disabled = True
            self.btn_delete_merge.disabled = True

    def on_text_setup_merge_label_changed(self, widget, event, data):
        if self.text_setup_merge_label.v_model and self.text_setup_merge_prop:
            self.btn_save_merge.disabled = False

    def on_text_setup_merge_prop_changed(self, widget, event, data):
        if (self.text_setup_merge_label.v_model or self.select_setup_merge_label.v_model != 'Other') \
                and self.text_setup_merge_prop:
            self.btn_save_merge.disabled = False

    def refresh_select_setup_merge(self):
        res1 = get_label_properties(self.neo)
        res2 = get_merge_on(self.neo)
        if res1:
            self.label_properties = {k: ','.join(i) for k, i in res1[0]['map'].items() if
                                     not k in ['_File_', '_MergeOn_', '_Metadata_']}
            if res2:
                self.label_properties.update(res2[0]['map'].items())
        else:
            self.label_properties = {}
        cur_selection = self.select_setup_merge_label.v_model
        self.select_setup_merge_label.items = ['Other'] + list(self.label_properties.keys())
        if cur_selection in self.select_setup_merge_label.items:
            pass
        else:
            self.select_setup_merge_label.v_model = 'Other'
        self.on_select_setup_merge_label_changed(None, None, None)

    def refresh_out_setup_merge(self):
        res = get_merge_on(self.neo)
        self.out_setup_merge.clear_output()
        if res:
            self.merge_on = res[0]['map']
        else:
            self.merge_on = {}
        with self.out_setup_merge:
            self.pp.pprint(self.merge_on)

    def render(self):
        if self.neo:
            self.refresh_col_list_files()
            self.refresh_selected_files_stats()
            self.refresh_select_edit_selected()
            self.refresh_select_setup_merge()
            self.refresh_out_setup_merge()
