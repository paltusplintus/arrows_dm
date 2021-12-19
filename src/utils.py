import re
import numpy as np

def get_next_number(lst:list, regex=r'^text_field_(\d+)\.\w+?$', zfill = 4):
    numbers = []
    for filename in lst:
        if re.match(regex, filename):
            numbers.append(int(re.findall(regex, filename)[0]))
    if numbers:
        max_number = np.max(numbers)
    else:
        max_number = 0
    next_number = max_number + 1
    return str(next_number).zfill(zfill)