import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from IPython.display import HTML

def sparkline(data, figsize=(10, 3), **kwags):
  fig, ax = plt.subplots(1, 1, figsize=figsize, **kwags)
  
  ax.plot(data, 'w')

  for k,v in ax.spines.items():
    v.set_visible(False)
    
  ax.set_xticks([])
  ax.set_yticks([])

  ymax = max(data)
  xmax = data.index(ymax)
  plt.plot(xmax, ymax, 'g.', markersize=20, alpha=0.5)

  ymin = min(data)
  xmin = data.index(ymin)
  plt.plot(xmin, ymin, 'r.', markersize=20, alpha=0.5)
  
  vert_lines = [x for x in range(0, len(data) + 1, 24)]
  for v in vert_lines:
    plt.axvline(x=v, color="white", alpha=0.1, ls="--")

  img = BytesIO()
  plt.savefig(img, transparent=True, bbox_inches='tight')
  img.seek(0)
  plt.close()

  return HTML('<img src="data:image/png;base64,{}" class="img-fluid"/>'.format(base64.b64encode(img.read()).decode("UTF-8")))