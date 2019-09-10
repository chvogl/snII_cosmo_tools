# snII_cosmo_tools

## Installation instructions
```
git clone https://github.com/chvogl/snII_cosmo_tools.git
cd snII_cosmo_tools
conda env create -f env.yml
conda activate snII_cosmo_tools
python setup.py install
cd snII_cosmo_tools
```
Download the redshift data ([glade](https://drive.google.com/file/d/1pMsBluOxjmcv9FVdKGG1shpPMxtieX9-/view?usp=sharing), [2dF](https://drive.google.com/file/d/1YtgEEe9rA0IVe1woP3dhr9hH0MU3YxWr/view?usp=sharing), [sdss](https://drive.google.com/file/d/1D7yb8qt7JwnloyQccREfP1Lfgkqq1UhF/view?usp=sharing)) from google drive and move it into the `redshift_data` folder.
To enable the ipyaladin widget, execute the following:
```
jupyter nbextension enable --py widgetsnbextension
jupyter nbextension enable --py --sys-prefix ipyaladin
```
Now you can launch the main notebook `target_selection.ipynb` by running:
```
jupyter-notebook target_selection.ipynb
```
