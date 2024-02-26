# Safari Bingo Cards
Fun proof of concept to generate random wildlife bingo cards for safaris with data from Wikipedia.

<p align="center">
  <img width="600" alt="Example bingo card showing a 4x4 grid of Sub-Saharan African wildlife" src="example.jpg">
</p>

# Usage

```console
$ ./generate.py -i data/animals.csv -o out.jpg
```

# TODO

- Credit photographers — these photos are all some variation of CC-BY so we need to give attribution
- Add filtering by region — the metadata already exists, though perhaps needs to be adjusted
- Refactor — perhaps needs to be more object oriented
- Make a web frontend — I can imagine a light frontend that would shuffle the images in realtime and allow generation of a number of cards

# License
This work is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).

The license allows you to use and modify the work for personal and commercial purposes, but if you distribute the work you must provide users with a means to access the source code for the version you are distributing. Read more about the [GPLv3 at TL;DR Legal](https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)).