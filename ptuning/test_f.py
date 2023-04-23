import os

import shutil
files = os.listdir('./')

res_file = []
for f in files:
    if os.path.isdir(f) and f.startswith(PREFIX_CHECKPOINT_DIR+"-"):
        name,num = f.split('-')
        num = int(num)
        res_file.append((name,num))

res_file.sort(key=lambda x:x[1])

if (len(res_file) > 5):
    name,num = res_file[0]
    shutil.rmtree(name+'-'+str(num))

