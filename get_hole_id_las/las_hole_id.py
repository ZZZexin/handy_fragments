import os

import lasio
import pandas as pd





def main():
    current_path = os.path.dirname(__file__)
    load_dir = os.path.join(current_path, r'load_dir')
    out_dir = os.path.join(current_path, r'out_dir')
    las_files = []
    hole_id = []
    for dirpath, _, filenames in os.walk(load_dir):
        for filename in filenames:
            if filename.lower().endswith(".las"):
                las_files.append(os.path.join(dirpath, filename))
                hole_id.append(filename.replace(".las", ""))
    
    second_col = []
    third_col = []
    for las_path in las_files:
        las = lasio.read(las_path)
        if las.params['SRC'].value == "Yes":
            second_col.append("True")
        else: second_col.append("False")

        if las.well['FLD'].value == "Roy Hill Minesite" or \
            las.well['FLD'].value == "ROY HILL":
            third_col.append("True")
        else: third_col.append("False")    

    df = {"Hole": hole_id,
          "Source_id": second_col,
          "Field": third_col          
          }
    df = pd.DataFrame(df)
    df.to_csv(os.path.join(out_dir,"rhio_sum.csv"))


if __name__ == "__main__":
    main()