import matplotlib as mpl

def normal_style():
    # set plotting
    fs = 10
    lw = 1.5
    dpi = 400

    # set figure style
    setting = {'dpi': dpi,
            'figsize': [6, 4]}
    mpl.rc('figure', **setting)

    # set line style
    setting = {'linewidth': 1.5,
            'color': 'black'}
    mpl.rc('lines', **setting)

    # set font style
    setting = {'family' : 'serif',
            'weight' : 'normal',
            'size'   : fs + 5}
    mpl.rc('font', **setting)
    mpl.rcParams['font.serif'] = ['Helvetica'] + ["WenQuanYi Micro Hei"] + ["SimHei"] + mpl.rcParams['font.serif']

    # set savefig style
    setting = {'dpi': dpi,
            'bbox': 'tight',
            'format': 'png'}
    mpl.rc('savefig', **setting)

    # set tick style
    setting = {'labelsize': fs-2}
    mpl.rc(['xtick', 'ytick'], **setting)

    # set legend style
    setting = {'fontsize': fs + 3}
    mpl.rc('legend', **setting)