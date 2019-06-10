from model import ncf
from pdb import set_trace

ncf_models = ncf(input_path='./collection/user_tracks.gz',
                 num_negatives=4)

ncf_models.get_models()

ncf_models.load_models()
hit_ratio = ncf_models.hit_ratio()
