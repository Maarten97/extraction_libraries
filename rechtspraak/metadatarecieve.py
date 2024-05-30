import rechtspraak_extractor as rex


def get_metadata():
    rex.get_rechtspraak_metadata(save_file='y')


if __name__ == '__main__':
    get_metadata()
