import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64

from io import BytesIO

def sparkline(data, figsize=(4, 0.25), **kwags):
    """
    Returns a HTML image tag containing a base64 encoded sparkline style plot
    """
    data = list(data)

    fig, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
    ax.plot(data)
    for k,v in ax.spines.items():
        v.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    plt.plot(len(data) - 1, data[len(data) - 1], 'r.')

    ax.fill_between(range(len(data)), data, len(data)*[min(data)], alpha=0.1)

    img = BytesIO()
    plt.savefig(img, transparent=True, bbox_inches='tight')
    img.seek(0)
    plt.close()

    #return base64.b64encode(img.read()).decode("UTF-8")
    return '<img src="data:image/png;base64,{}"/>'.format(base64.b64encode(img.read()).decode("UTF-8"))


# if __name__ == "__main__":
#     values = [
#         [1,2,3,4,5,6,7,8,9,10],
#         [7,10,12,18,2,8,10,6,7,12],
#         [10,9,8,7,6,5,4,3,2,1]
#     ]

#     with open("/tmp/foo.html", "w") as file:
#         for value in values:
#             file.write('<div><img src="data:image/png;base64,{}"/></div>'.format(sparkline(value)))