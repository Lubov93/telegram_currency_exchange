import matplotlib.pyplot as plt


def history_plot(data, *, cur1=None, cur2=None) -> 'matplotlib plot':
    lst1, lst2 = zip(*data)

    plt.figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')

    plt.plot(lst1, lst2, )
    if cur1 and cur2:
        plt.ylabel('{} to {}'.format(cur1, cur2))
    plt.xlabel('date')
    if len(lst1) > 8:
        plt.xticks(lst1[::int(len(lst1)/8)], rotation=45)
        plt.subplots_adjust(bottom=0.25)
    plt.subplots_adjust(left=0.15)
    return plt
