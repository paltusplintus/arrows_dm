export NEO4J_HOST=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=admin
venv/bin/voila "Arrows Data Mananger.ipynb" --enable_nbextensions=True --autoreload=True --MappingKernelManager.cull_interval=60 --MappingKernelManager.cull_idle_timeout=3600 &
