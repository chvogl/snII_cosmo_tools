

def get_aladin_coords(targets, index):
    return (targets.iloc[index].RA.replace(':', ' ') +
            targets.iloc[index].DEC.replace(':', ' '))
