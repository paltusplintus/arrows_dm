# sudo apt install python3-venv
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m jupyter nbextension enable --py --sys-prefix qgrid
venv/bin/python -m jupyter nbextension enable --py --sys-prefix ipyvuetify
venv/bin/python -m jupyter serverextension enable voila --sys-prefix
# to make voila work with qgrid follow https://github.com/voila-dashboards/voila/issues/72
# in venv\share\jupyter\nbextensions\qgrid\index.js
# Changed:
# define(["@jupyter-widgets/base","base/js/dialog"], function(__WEBPACK_EXTERNAL_MODULE_139__, __WEBPA...........
# To:
# define(["@jupyter-widgets/base"], function(__WEBPACK_EXTERNAL_MODULE_139__, __WEBPA
# for qgrid v1.3.1 the updated file is stored in misc/index.js
cp misc/index.js venv/share/jupyter/nbextensions/qgrid/index.js
