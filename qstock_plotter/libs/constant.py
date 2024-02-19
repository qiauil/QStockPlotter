from .helpers import GeneralDataClass

ZOOM_MODEL=GeneralDataClass(
    AUTO_RANGE=0,
    FIXED_RATIO=1,
    FIXED_YRANGE=2,
)

YLOC_MODEL=GeneralDataClass(
    FREE=0, # allow free move, y_loc is changed as while y_center is not changed
    DATA_CENTERED=1, # doesn't allow free move, y_loc is always the center of the data
    FIXED=2, # dosen't allow free move, y_loc is not changed
)

SCALE_LOC_MODEL=GeneralDataClass(
    CENTRAL=0,
    LEFT=1,
    RIGHT=2,
)
