import argparse
from model import ncf
from pdb import set_trace

parser = argparse.ArgumentParser()
parser.add_argument('user', type=int)
args = parser.parse_args()

ncf_models = ncf(input_path='./collection/user_tracks.gz',
                 num_negatives=4)

ncf_models.get_models()

ncf_models.load_models()

print(ncf_models.get_user_results(user=args.user).iloc[:10])
