# miscQR

## Example
```sh
python3 -i -m src.whim toshs.github.io/miscQR/a.html -6
>>> ret
{'toshs.github.io/miscQR/b.html': <PIL.Image.Image image mode=RGB size=29x29 at ...
 ... 'toshs.github.io/miscQR/3.html': <PIL.Image.Image image mode=RGB size=29x29 at 0x116DF2438>}

>>> ret['toshs.github.io/miscQR/b.html'].show()
```

![Sample QR](./docs/aorb.png)