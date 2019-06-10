from model import ncf
from pdb import set_trace

ncf_models = ncf(matrix_path='model_input.gz',
                 num_negatives=4)

ncf_models.load()

ncf_models.get_models()
ncf_models.summary()

ncf_models.train()
