# Process vsi image of vessels

Install numpy, python-bioformats:

```bash
pip3 install --user javabridge numpy python-bioformats matplotlib tqdm
```

To see help run:
```bash
python3 vessels.py --help
```

Example how to load files and save to npy object:
```bash
python3 vessels.py -f Folder/file.vsi
```

Example how to load from npy object:
```bash
python3 vessels.py -f Folder/file.vsi -l
```