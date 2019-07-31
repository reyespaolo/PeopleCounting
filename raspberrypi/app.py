from peoplecounter import PeopleCounting
from argparse import ArgumentParser

parser = ArgumentParser(description="PeopleCounting")
parser.add_argument('--config_path', dest='config_path', default="settings.ini", help='path to settinsg.ini')
args = parser.parse_args()

# Start People Counting
peoplecounting = PeopleCounting()
peoplecounting.go_config(config_path=args.config_path)
