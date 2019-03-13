# miscQR

## Install
### Manual

```sh
git clone https://github.com/toshs/misqr.git
cd misqr
pip3 install -e .
```

## Example

### Generate Whimq
```sh
python3 -i -m misqr.whim toshs.github.io/misqr/a.html -6
>>> ret
{'toshs.github.io/misqr/b.html': <PIL.Image.Image image mode=RGB size=29x29 at ...
 ... 'toshs.github.io/misqr/3.html': <PIL.Image.Image image mode=RGB size=29x29 at 0x116DF2438>}

>>> ret['toshs.github.io/misqr/b.html'].show()
```

![Sample QR](./docs/aorb.png)

### Generate Qash
```sh
qash toshs.github.io/misqr/a.html
```
