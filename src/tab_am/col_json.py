import ipyvuetify as v
from neointerface import NeoInterface
import ipywidgets as w
import json
from src.neo_utils import get_loaded_files, load_content, extract_jsons, delete_content
from src.utils import get_next_number


class ColJson(v.Col):
    TEXTFIELD_PREFIX = "text_field_"

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.neo = None
        self.split1 = v.Divider()
        self.text_area = v.Textarea(v_model="", hint="Paste json content from Arrows.app")
        self.btn_upload = v.Btn(children=["Load text"])
        self.btn_upload.on_event('click', self.on_btn_upload_clicked)
        self.split2 = v.Divider()
        self.html1 = v.Html(tag="div", style_='font-weight: bold', children = ["OR"])
        self.file_upload = w.FileUpload(label="Select files", accept=".json, .csv", enabled=False)
        self.cont_file_upload = w.VBox([self.file_upload])
        self.btn_file_upload = v.Btn(children=["Load file(s)"])
        self.btn_file_upload.on_event('click', self.on_btn_file_upload_clicked)
        self.out = w.Output()
        self.children = [
            self.split1,
            self.text_area,
            self.btn_upload,
            self.split2,
            self.html1,
            w.VBox([
                self.cont_file_upload,
                self.btn_file_upload,
            ],
                layout=w.Layout(align_items='center')
            ),
            self.out
        ]
        self.render()

    def load_content(self, content: dict, filename: str):
        try:
            load_content(neo=self.neo, filename=filename, content=content)
            extract_jsons(neo=self.neo, merge_on=self.parent.get_merge_on())
            self.out.clear_output()
            with self.out:
                print("json subgraph loaded successfully")
            self.parent.col_preview.render()
        except Exception as e:
            self.out.clear_output()
            with self.out:
                print("""
        Could not load json subgraph.
        Please check that you provided all nodes with labels and at least 1 property and all relationships with types.
                        """)
                print(e.message, e.args)
            delete_content(neo=self.neo, names=[filename])

    def on_btn_upload_clicked(self, widget, event, data):
        try:
            dct = json.loads(self.text_area.v_model)
        except:
            with self.out:
                print("ERROR: invalid json format, please check the content being loaded")
        files_loaded = get_loaded_files(self.neo)
        cur_filename = self.TEXTFIELD_PREFIX + get_next_number(files_loaded) + ".json"
        self.load_content(content=self.text_area.v_model, filename=cur_filename)
        self.text_area.v_model = ""  # clearing the text area

    def on_btn_file_upload_clicked(self, widget, event, data):
        for key, item in self.file_upload.value.items():
            content = item['content'].decode('utf-8')
            file_ = key.split(".")
            self.load_content(content=content, filename=key)

        self.file_upload = w.FileUpload(accept=".json, .csv", enabled=False)
        self.cont_file_upload.children = [self.file_upload]
        self.parent.col_preview.render()

    def render(self):
        pass
