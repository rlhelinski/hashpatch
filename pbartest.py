import progressbar, time

#widgets = ["Progress: ", progressbar.Bar(marker="=", left="[", right="]"), " ", progressbar.Percentage() ]
widgets = ["Progress: ", progressbar.Bar(marker="=", left="[", right="]"), " ", progressbar.Fraction(), " ", progressbar.Percentage() ]
pbar = progressbar.ProgressBar(widgets=widgets, maxval=100)
pbar.start()
for i in range(1000):
	time.sleep(0.007)
	pbar.update(i, 1000)
pbar.finish()
